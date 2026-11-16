// FileOptimizer Community Portable — independently compiled Win64 root launcher.
// Copyright (c) 2026 FileOptimizer Community Portable builder contributors.
// SPDX-License-Identifier: MIT (launcher only; FileOptimizer is AGPL).
// Scope: private INI/log transaction, child-only temporary directory,
// and one upstream-confirmed HKCU browser-emulation value. No broad harvesting.
#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <string>
#include <vector>
#include <algorithm>
#include <cstdint>
#include <cstring>
#include <bcrypt.h>

namespace {
using W = std::wstring;
const wchar_t *kRegPath = L"Software\\Microsoft\\Internet Explorer\\Main\\FeatureControl\\FEATURE_BROWSER_EMULATION";
const wchar_t *kRegName = L"FileOptimizer64.exe";
const wchar_t *kFiles[] = {L"FileOptimizer.ini", L"FileOptimizer.log"};
struct JournalHeader { DWORD magic; DWORD present; DWORD type; DWORD bytes; };
constexpr DWORD kMagic = 0x46505231; // FPR1
W join(const W &a, const W &b) { return a + L"\\" + b; }
void fail(const W &message) { MessageBoxW(nullptr, message.c_str(), L"FileOptimizer Portable", MB_OK|MB_ICONERROR); }
bool exists(const W &s) { return GetFileAttributesW(s.c_str()) != INVALID_FILE_ATTRIBUTES; }
bool regular(const W &s) { DWORD a=GetFileAttributesW(s.c_str()); return a!=INVALID_FILE_ATTRIBUTES && !(a&(FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT)); }
bool safeDir(const W &s) {
 DWORD a=GetFileAttributesW(s.c_str());
 if (a == INVALID_FILE_ATTRIBUTES) { if (!CreateDirectoryW(s.c_str(),nullptr)) return false; a=GetFileAttributesW(s.c_str()); }
 return (a&FILE_ATTRIBUTE_DIRECTORY) && !(a&FILE_ATTRIBUTE_REPARSE_POINT);
}
bool createTree(const W &s) {
 size_t pos=s.find_last_of(L'\\');
 if (pos!=W::npos && pos>2 && !exists(s.substr(0,pos)) && !createTree(s.substr(0,pos))) return false;
 return safeDir(s);
}
W timestamp() { SYSTEMTIME s{}; GetLocalTime(&s); wchar_t buf[64];
 swprintf_s(buf, L"%04u%02u%02u-%02u%02u%02u-%04u",s.wYear,s.wMonth,s.wDay,s.wHour,s.wMinute,s.wSecond,GetCurrentProcessId()); return buf; }
void logline(const W &p, const char *line) {
 if(exists(p) && !regular(p))return;
 HANDLE f=CreateFileW(p.c_str(), FILE_APPEND_DATA,FILE_SHARE_READ,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(f==INVALID_HANDLE_VALUE)return; DWORD b; WriteFile(f,line,(DWORD)strlen(line),&b,nullptr); WriteFile(f,"\r\n",2,&b,nullptr); FlushFileBuffers(f); CloseHandle(f);
}
bool writeAtomic(const W &p, const void *data, DWORD n) {
 W temp=p+L".pending"; HANDLE h=CreateFileW(temp.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(h==INVALID_HANDLE_VALUE) return false;
 DWORD done=0; bool ok=WriteFile(h,data,n,&done,nullptr)!=0 && done==n && FlushFileBuffers(h);
 CloseHandle(h); if(!ok) return false;
 return MoveFileExW(temp.c_str(),p.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
}
bool readAll(const W &p, std::vector<BYTE> &v) {
 if(!regular(p))return false;
 HANDLE h=CreateFileW(p.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(h==INVALID_HANDLE_VALUE)return false;
 LARGE_INTEGER sz{}; bool ok=GetFileSizeEx(h,&sz)!=0 && sz.QuadPart>=0 && sz.QuadPart<=1024*1024;
 if(ok){v.resize((size_t)sz.QuadPart); DWORD got=0; ok=ReadFile(h,v.data(),(DWORD)v.size(),&got,nullptr)!=0&&got==v.size();}
 CloseHandle(h);return ok;
}
bool sha256(const W &file, std::vector<BYTE> &out) {
 HANDLE f=CreateFileW(file.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(f==INVALID_HANDLE_VALUE)return false;
 BCRYPT_ALG_HANDLE alg=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;
 NTSTATUS st=BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,nullptr,0);
 if(st<0){CloseHandle(f);return false;}
 st=BCryptCreateHash(alg,&hash,nullptr,0,nullptr,0,0);
 BYTE buf[65536];DWORD got=0;
 if(st>=0){
   for(;;) {
     if(!ReadFile(f,buf,sizeof(buf),&got,nullptr)){st=-1;break;}
     if(got==0)break;
     st=BCryptHashData(hash,buf,got,0);if(st<0)break;
   }
 }
 if(st>=0){out.resize(32);st=BCryptFinishHash(hash,out.data(),(ULONG)out.size(),0);}
 if(hash)BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(alg,0);CloseHandle(f);
 return st>=0;
}
bool equalFiles(const W &a,const W &b){
 std::vector<BYTE>x,y;return sha256(a,x)&&sha256(b,y)&&x==y;
}
bool backupCopy(const W &src, const W &dst, const W &backupRoot, const W &runid) {
 if(!regular(src))return !exists(src); // reject symlink/junction / directory
 if(exists(dst)) {
   if(!regular(dst))return false;
   W saved=join(backupRoot,runid+L"-"+dst.substr(dst.find_last_of(L'\\')+1));
   if(!CopyFileW(dst.c_str(),saved.c_str(),TRUE)||!equalFiles(dst,saved))return false;
 }
 W staging=dst+L".pending";
 if(exists(staging))return false; // never remove unrecognized earlier transaction
 if(!CopyFileW(src.c_str(),staging.c_str(),TRUE))return false;
 LARGE_INTEGER a{},b{}; HANDLE x=CreateFileW(src.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
 HANDLE y=CreateFileW(staging.c_str(),GENERIC_READ,FILE_SHARE_READ,nullptr,OPEN_EXISTING,0,nullptr);
 bool ok=x!=INVALID_HANDLE_VALUE&&y!=INVALID_HANDLE_VALUE&&GetFileSizeEx(x,&a)&&GetFileSizeEx(y,&b)&&a.QuadPart==b.QuadPart;
 if(x!=INVALID_HANDLE_VALUE)CloseHandle(x);if(y!=INVALID_HANDLE_VALUE)CloseHandle(y);
 if(!ok||!equalFiles(src,staging))return false;
 return MoveFileExW(staging.c_str(),dst.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
}
bool loadReg(DWORD &type,std::vector<BYTE> &data,bool &present){
 HKEY h=nullptr;LONG r=RegOpenKeyExW(HKEY_CURRENT_USER,kRegPath,0,KEY_QUERY_VALUE,&h);
 if(r==ERROR_FILE_NOT_FOUND){present=false;return true;}
 if(r!=ERROR_SUCCESS)return false;
 DWORD size=0; r=RegQueryValueExW(h,kRegName,nullptr,&type,nullptr,&size);
 if(r==ERROR_FILE_NOT_FOUND){present=false;RegCloseKey(h);return true;}
 if(r!=ERROR_SUCCESS||size>1024*1024){RegCloseKey(h);return false;}
 data.resize(size);r=RegQueryValueExW(h,kRegName,nullptr,&type,data.data(),&size);
 RegCloseKey(h);if(r!=ERROR_SUCCESS)return false;data.resize(size);present=true;return true;
}
bool snapshotReg(const W &p) {
 bool present=false;DWORD type=0;std::vector<BYTE> bytes;
 if(!loadReg(type,bytes,present))return false;
 JournalHeader j{kMagic,present?1u:0u,type,(DWORD)bytes.size()};
 std::vector<BYTE> payload(sizeof(j)+bytes.size());memcpy(payload.data(),&j,sizeof(j));
 if(!bytes.empty())memcpy(payload.data()+sizeof(j),bytes.data(),bytes.size());
 return writeAtomic(p,payload.data(),(DWORD)payload.size());
}
bool restoreReg(const W &p,const W &log) {
 if(!exists(p))return true;
 std::vector<BYTE> v; if(!readAll(p,v)||v.size()<sizeof(JournalHeader))return false;
 JournalHeader j{};memcpy(&j,v.data(),sizeof(j));
 if(j.magic!=kMagic||j.bytes!=v.size()-sizeof(j)||j.present>1)return false;
 bool present=false;DWORD type=0;std::vector<BYTE> current;
 if(!loadReg(type,current,present))return false;
 // Upstream writes REG_DWORD 11001. Preserve any other/changed host state.
 const DWORD expected=11001;
 bool matches=present&&type==REG_DWORD&&current.size()==sizeof(expected)&&memcmp(current.data(),&expected,sizeof(expected))==0;
 bool sameOriginal = (present==(j.present!=0)) && (!present || (type==j.type && current.size()==j.bytes && memcmp(current.data(),v.data()+sizeof(j),j.bytes)==0));
 if(sameOriginal)return DeleteFileW(p.c_str())!=0; // upstream never changed the key
 if(!matches) { logline(log,"Registry changed by another process or upstream behavior; journal retained; no host value was touched.");return false; }
 HKEY h=nullptr; LONG r=RegOpenKeyExW(HKEY_CURRENT_USER,kRegPath,0,KEY_SET_VALUE,&h);
 if(r!=ERROR_SUCCESS)return false;
 if(j.present)r=RegSetValueExW(h,kRegName,0,j.type,v.data()+sizeof(j),j.bytes);
 else r=RegDeleteValueW(h,kRegName);
 RegCloseKey(h);
 if(r!=ERROR_SUCCESS)return false;
 return DeleteFileW(p.c_str())!=0;
}
W quote(const W &s) {
 if(s.find_first_of(L" \t\n\v\"")==W::npos)return s;
 W out=L"\"";size_t slash=0;
 for(wchar_t c:s) {if(c==L'\\'){++slash;continue;}
 if(c==L'"'){out.append(slash*2+1,L'\\');out+=L'"';}
 else {out.append(slash,L'\\');out+=c;}slash=0;}
 out.append(slash*2,L'\\');out+=L'"';return out;
}
W cli(const W &exe) {
 int argc=0;LPWSTR *argv=CommandLineToArgvW(GetCommandLineW(),&argc);
 W c=quote(exe);if(argv){for(int i=1;i<argc;++i)c+=L" "+quote(argv[i]);LocalFree(argv);}return c;
}
}
int WINAPI wWinMain(HINSTANCE,HINSTANCE,LPWSTR,int){
 wchar_t path[32768]{};DWORD n=GetModuleFileNameW(nullptr,path,32768);
 if(!n||n>=32768){fail(L"Cannot determine launcher folder.");return 1;}
 W full=path;size_t at=full.find_last_of(L"\\/");if(at==W::npos)return 1;
 W root=full.substr(0,at), app=join(join(root,L"App"),L"FileOptimizer"),data=join(root,L"Data");
 W settings=join(data,L"Settings"),ctrl=join(data,L"Control"),backup=join(data,L"Backups"),temp=join(data,L"RuntimeTemp"),logs=join(data,L"Logs");
 W exe=join(app,L"FileOptimizer64.exe"),journal=join(ctrl,L"registry.journal"),marker=join(ctrl,L"active.run"),log=join(logs,L"launcher.log");
 if(!safeDir(root)||!safeDir(join(root,L"App"))||!safeDir(app)||!regular(exe)||!createTree(settings)||!createTree(ctrl)||!createTree(backup)||!createTree(temp)||!createTree(logs)){
   fail(L"The application or writable portable Data folder is missing, read-only or redirected. No host cleanup was attempted.");return 2;
 }
 W lockpath=join(ctrl,L"launcher.lock");
 if(exists(lockpath)&&!regular(lockpath)){fail(L"Unsafe launcher lock file (reparse point). Launch cancelled.");return 3;}
 HANDLE lock=CreateFileW(lockpath.c_str(),GENERIC_READ|GENERIC_WRITE,0,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
 if(lock==INVALID_HANDLE_VALUE){fail(L"Another portable launcher is running, or the Data folder cannot be locked.");return 3;}
 HANDLE upstream=OpenMutexW(SYNCHRONIZE,FALSE,L"FileOptimizer");
 if(upstream){CloseHandle(upstream);fail(L"FileOptimizer is already running (including a possible installed copy). Close it before launching Portable.");CloseHandle(lock);return 4;}
 W rid=timestamp();
 // Crash recovery: only app-private sidecars are recovered. Keep old Data versions as backups.
 if(exists(marker)) {
   logline(log,"Interrupted session found; reconciling only private App/FileOptimizer sidecars.");
   for(auto f:kFiles) if(exists(join(app,f))&&!backupCopy(join(app,f),join(settings,f),backup,rid)){
     fail(L"Recovery conflict. Files were preserved. Inspect Data\\Backups and Data\\Control.");CloseHandle(lock);return 5;
   }
   if(!restoreReg(journal,log)) {fail(L"Registry recovery is unresolved. No unrelated entries were changed. Inspect Data\\Control.");CloseHandle(lock);return 6;}
   for(auto f:kFiles) if(exists(join(app,f))&&!DeleteFileW(join(app,f).c_str())){
     fail(L"Could not clear recovered App sidecar. The original was retained safely.");CloseHandle(lock);return 18;
   }
   if(!DeleteFileW(marker.c_str())){fail(L"Unable to clear previous session marker.");CloseHandle(lock);return 7;}
 } else if(exists(journal)) {
   fail(L"Unexpected registry journal without a session marker; no data overwritten.");CloseHandle(lock);return 8;
 }
 // A writable application folder is essential: otherwise upstream falls back to %USERPROFILE%.
 W probe=join(app,L".fileoptimizer-portable-write-test");
 HANDLE hp=CreateFileW(probe.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_TEMPORARY,nullptr);
 if(hp==INVALID_HANDLE_VALUE){fail(L"App\\FileOptimizer is not writable; upstream could fall back to the Windows profile.");CloseHandle(lock);return 17;}
 CloseHandle(hp);if(!DeleteFileW(probe.c_str())){fail(L"Temporary write probe could not be removed.");CloseHandle(lock);return 19;}
 for(auto f:kFiles) {
   W src=join(settings,f),dst=join(app,f);
   if(exists(dst)){fail(L"Application-side settings/log files exist without a recovery marker. No file was overwritten.");CloseHandle(lock);return 9;}
   if(exists(src)&&(!regular(src)||!CopyFileW(src.c_str(),dst.c_str(),TRUE))){fail(L"Could not prepare portable configuration.");CloseHandle(lock);return 10;}
 }
 if(!snapshotReg(journal)){fail(L"Unable to snapshot browser registry value. Launch cancelled.");CloseHandle(lock);return 11;}
 const char active[]="FileOptimizer Portable active\n";
 if(!writeAtomic(marker,active,sizeof(active)-1)){fail(L"Unable to create recovery journal.");CloseHandle(lock);return 12;}
 // Only the application's CHILD process and its descendants inherit these paths.
 SetEnvironmentVariableW(L"TEMP",temp.c_str());SetEnvironmentVariableW(L"TMP",temp.c_str());
 SetEnvironmentVariableW(L"WEBVIEW2_USER_DATA_FOLDER",join(data,L"WebView2").c_str());
 createTree(join(data,L"WebView2"));
 W cmd=cli(exe);std::vector<wchar_t> cmdline(cmd.begin(),cmd.end());cmdline.push_back(0);
 STARTUPINFOW si{};si.cb=sizeof(si);PROCESS_INFORMATION pi{};
 DWORD flags=CREATE_SUSPENDED|CREATE_UNICODE_ENVIRONMENT;
 if(!CreateProcessW(exe.c_str(),cmdline.data(),nullptr,nullptr,FALSE,flags,nullptr,app.c_str(),&si,&pi)){
   fail(L"FileOptimizer could not start. Its private data and recovery journal were preserved.");CloseHandle(lock);return 13;
 }
 HANDLE job=CreateJobObjectW(nullptr,nullptr);
 if(!job||!AssignProcessToJobObject(job,pi.hProcess)){
   TerminateProcess(pi.hProcess,1);WaitForSingleObject(pi.hProcess,10000);
   if(job)CloseHandle(job);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);
   fail(L"Windows could not track FileOptimizer child processes. Launch cancelled safely.");CloseHandle(lock);return 14;
 }
 ResumeThread(pi.hThread);CloseHandle(pi.hThread);
 WaitForSingleObject(pi.hProcess,INFINITE);DWORD exitCode=1;GetExitCodeProcess(pi.hProcess,&exitCode);CloseHandle(pi.hProcess);
 // Do not move a live plugin's logs/configuration. Never terminate a worker to clean traces.
 bool idle=false;DWORD started=GetTickCount();
 while(GetTickCount()-started<120000) {
   JOBOBJECT_BASIC_ACCOUNTING_INFORMATION a{};
   if(QueryInformationJobObject(job,JobObjectBasicAccountingInformation,&a,sizeof(a),nullptr) && a.ActiveProcesses==0){idle=true;break;}
   Sleep(400);
 }
 CloseHandle(job);
 if(!idle){logline(log,"Child processes still active after 120 seconds; leaving live files and journal for safe recovery.");fail(L"A plugin or browser process has not exited. Portable data is preserved; retry after it closes.");CloseHandle(lock);return 15;}
 bool ok=true;
 for(auto f:kFiles) if(exists(join(app,f))) {
   if(!backupCopy(join(app,f),join(settings,f),backup,rid)){ok=false;break;}
 }
 if(ok)for(auto f:kFiles) if(exists(join(app,f))&&!DeleteFileW(join(app,f).c_str()))ok=false;
 if(ok)ok=restoreReg(journal,log);
 if(ok)ok=DeleteFileW(marker.c_str())!=0;
 if(!ok){logline(log,"Cleanup incomplete; original files and journal remain for recovery.");fail(L"Portable cleanup could not finish. Your data was preserved in Data and App. Do not delete either folder.");CloseHandle(lock);return 16;}
 logline(log,"Successful portable application session and selective registry restoration.");CloseHandle(lock);
 return (int)exitCode;
}
