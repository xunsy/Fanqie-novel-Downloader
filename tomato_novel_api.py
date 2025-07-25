#!/usr/bin/env python3
""#line:2
import requests #line:3
import json #line:4
import sys #line:5
import urllib .parse #line:6
import time #line:7
from typing import Optional #line:8
class TomatoNovelAPI :#line:9
    def __init__ (O0OO000OO0000O0OO ):#line:10
        O0OO000OO0000O0OO .base_url ="http://read.tutuxka.top"#line:11
        O0OO000OO0000O0OO .session =requests .Session ()#line:12
        O0OO000OO0000O0OO .session .headers .update ({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36','Referer':O0OO000OO0000O0OO .base_url ,'DNT':'1'})#line:13
        O0OO000OO0000O0OO .timeout =30 #line:14
        O0OO000OO0000O0OO .max_retries =3 #line:15
        O0OO000OO0000O0OO .retry_delay =2 #line:16
    def _make_request_with_retry (O0O0OOOO00OO0OOOO ,O0O00O0OOO000OO0O :str ,O0O000O0O0O0OO0OO :Optional [dict ]=None )->Optional [dict ]:#line:17
        ""#line:18
        for O0O00O000O0OOO0OO in range (O0O0OOOO00OO0OOOO .max_retries ):#line:19
            try :#line:20
                print (f"尝试请求 (第{O0O00O000O0OOO0OO + 1}次): {O0O00O0OOO000OO0O}")#line:21
                OOOO0O0O0OOO00O0O =O0O0OOOO00OO0OOOO .session .get (O0O00O0OOO000OO0O ,params =O0O000O0O0O0OO0OO ,timeout =O0O0OOOO00OO0OOOO .timeout )#line:22
                OOOO0O0O0OOO00O0O .raise_for_status ()#line:23
                return OOOO0O0O0OOO00O0O .json ()#line:24
            except requests .exceptions .Timeout :#line:25
                print (f"请求超时 (第{O0O00O000O0OOO0OO + 1}次)")#line:26
                if O0O00O000O0OOO0OO <O0O0OOOO00OO0OOOO .max_retries -1 :#line:27
                    print (f"等待 {O0O0OOOO00OO0OOOO.retry_delay} 秒后重试...")#line:28
                    time .sleep (O0O0OOOO00OO0OOOO .retry_delay )#line:29
                else :#line:30
                    print (f"请求超时，已达到最大重试次数 ({O0O0OOOO00OO0OOOO.max_retries})")#line:31
            except requests .exceptions .HTTPError as O00OO0OO0OO0OO00O :#line:32
                if O00OO0OO0OO0OO00O .response .status_code ==504 :#line:33
                    print (f"服务器网关超时 (504) - 第{O0O00O000O0OOO0OO + 1}次")#line:34
                    if O0O00O000O0OOO0OO <O0O0OOOO00OO0OOOO .max_retries -1 :#line:35
                        print (f"等待 {O0O0OOOO00OO0OOOO.retry_delay * 2} 秒后重试...")#line:36
                        time .sleep (O0O0OOOO00OO0OOOO .retry_delay *2 )#line:37
                    else :#line:38
                        print (f"服务器持续超时，建议稍后再试")#line:39
                else :#line:40
                    print (f"HTTP错误: {O00OO0OO0OO0OO00O}")#line:41
                    break #line:42
            except requests .RequestException as O00OO0OO0OO0OO00O :#line:43
                print (f"网络请求失败: {O00OO0OO0OO0OO00O}")#line:44
                if O0O00O000O0OOO0OO <O0O0OOOO00OO0OOOO .max_retries -1 :#line:45
                    print (f"等待 {O0O0OOOO00OO0OOOO.retry_delay} 秒后重试...")#line:46
                    time .sleep (O0O0OOOO00OO0OOOO .retry_delay )#line:47
                else :#line:48
                    print (f"网络连接失败，已达到最大重试次数")#line:49
            except json .JSONDecodeError as O00OO0OO0OO0OO00O :#line:50
                print (f"解析响应JSON失败: {O00OO0OO0OO0OO00O}")#line:51
                break #line:52
        return None #line:53
    def search_novels (OO0OO0OOO0O0O0OOO ,O0O0O00OOO0OO000O ,OO0OO000000O0O000 =0 ,O00000OOOO00OO00O =1 ):#line:54
        ""#line:55
        O0O0OOOO0O000OO00 =urllib .parse .quote (O0O0O00OOO0OO000O )#line:56
        O0OO0O00O0O000OO0 =f"{OO0OO0OOO0O0O0OOO.base_url}/search.php?key={O0O0OOOO0O000OO00}&offset={OO0OO000000O0O000}&tab_type={O00000OOOO00OO00O}"#line:57
        return OO0OO0OOO0O0O0OOO ._make_request_with_retry (O0OO0O00O0O000OO0 )#line:58
    def get_novel_info (OO0000OO0O0000O00 ,OO00O0OO000OO00O0 ):#line:59
        ""#line:60
        O00O0O000O0O0OO00 =f"{OO0000OO0O0000O00.base_url}/content.php?book_id={OO00O0OO000OO00O0}"#line:61
        return OO0000OO0O0000O00 ._make_request_with_retry (O00O0O000O0O0OO00 )#line:62
    def get_chapter_content (OOOOO0OOO0OO000OO ,O00OO000OOO0O0OOO ):#line:63
        ""#line:64
        O00OOO00OO00000OO =f"{OOOOO0OOO0OO000OO.base_url}/content.php?item_ids={O00OO000OOO0O0OOO}&api_type=full"#line:65
        return OOOOO0OOO0OO000OO ._make_request_with_retry (O00OOO00OO00000OO )#line:66
    def get_book_details (O0O0OO0O000OOO000 ,O0000OO0OOOOO0O0O ):#line:67
        ""#line:68
        O0O000O0O0O00OOO0 =f"{O0O0OO0O000OOO000.base_url}/book.php?bookId={O0000OO0OOOOO0O0O}"#line:69
        return O0O0OO0O000OOO000 ._make_request_with_retry (O0O000O0O0O00OOO0 )#line:70
    def download_full_novel (O0OO0OO000O0O0O0O ,O00000O0OOO000OO0 ,O0OOO0OO00O0OO000 ):#line:71
        ""#line:72
        if isinstance (O0OOO0OO00O0OO000 ,list ):#line:73
            O00OO0OOOOO00OO0O =','.join (O0OOO0OO00O0OO000 )#line:74
        else :#line:75
            O00OO0OOOOO00OO0O =O0OOO0OO00O0OO000 #line:76
        OO0OOOO0000000OO0 =f"{O0OO0OO000O0O0O0O.base_url}/full.php?book_id={O00000O0OOO000OO0}&item_ids={O00OO0OOOOO00OO0O}"#line:77
        OOO0OOO0OO00000OO =O0OO0OO000O0O0O0O ._make_request_with_retry (OO0OOOO0000000OO0 )#line:78
        if OOO0OOO0OO00000OO :#line:79
            if not isinstance (OOO0OOO0OO00000OO ,list ):#line:80
                print (f"下载整本小说失败，服务器返回了非列表类型: {type(OOO0OOO0OO00000OO)}")#line:81
                return None #line:82
            return {"success":True ,"data":{"items":OOO0OOO0OO00000OO }}#line:83
        return None #line:84
def main ():#line:85
    ""#line:86
    OOOO0OOOO0OOOOO00 =TomatoNovelAPI ()#line:87
    if len (sys .argv )<2 :#line:88
        print ("使用方法:")#line:89
        print ("  搜索小说: python tomato_novel_api.py search <关键词>")#line:90
        print ("  获取小说信息: python tomato_novel_api.py novel_info <书籍ID>")#line:91
        print ("  获取书籍详细信息: python tomato_novel_api.py book_details <书籍ID>")#line:92
        print ("  获取章节内容: python tomato_novel_api.py chapter_content <章节ID>")#line:93
        print ("  下载整本小说: python tomato_novel_api.py download_full <书籍ID> <章节ID列表>")#line:94
        return #line:95
    O00OOOO00O0O0O000 =sys .argv [1 ]#line:96
    if O00OOOO00O0O0O000 =="search":#line:97
        if len (sys .argv )<3 :#line:98
            print ("请提供搜索关键词")#line:99
            return #line:100
        O0O0O0OO0OOO00O0O =sys .argv [2 ]#line:101
        print (f"正在搜索: {O0O0O0OO0OOO00O0O}")#line:102
        OOOO0OOO00OOO0OOO =OOOO0OOOO0OOOOO00 .search_novels (O0O0O0OO0OOO00O0O )#line:103
        if OOOO0OOO00OOO0OOO :#line:104
            print (json .dumps (OOOO0OOO00OOO0OOO ,ensure_ascii =False ,indent =2 ))#line:105
        else :#line:106
            print ("搜索失败")#line:107
    elif O00OOOO00O0O0O000 =="novel_info":#line:108
        if len (sys .argv )<3 :#line:109
            print ("请提供书籍ID")#line:110
            return #line:111
        O00O0O0O00O0OOOO0 =sys .argv [2 ]#line:112
        print (f"正在获取书籍信息: {O00O0O0O00O0OOOO0}")#line:113
        OOOO0OOO00OOO0OOO =OOOO0OOOO0OOOOO00 .get_novel_info (O00O0O0O00O0OOOO0 )#line:114
        if OOOO0OOO00OOO0OOO :#line:115
            print (json .dumps (OOOO0OOO00OOO0OOO ,ensure_ascii =False ,indent =2 ))#line:116
        else :#line:117
            print ("获取书籍信息失败")#line:118
    elif O00OOOO00O0O0O000 =="book_details":#line:119
        if len (sys .argv )<3 :#line:120
            print ("请提供书籍ID")#line:121
            return #line:122
        OO0O00000O000OOO0 =sys .argv [2 ]#line:123
        print (f"正在获取书籍详细信息: {OO0O00000O000OOO0}")#line:124
        OOOO0OOO00OOO0OOO =OOOO0OOOO0OOOOO00 .get_book_details (OO0O00000O000OOO0 )#line:125
        if OOOO0OOO00OOO0OOO :#line:126
            print (json .dumps (OOOO0OOO00OOO0OOO ,ensure_ascii =False ,indent =2 ))#line:127
        else :#line:128
            print ("获取书籍详细信息失败")#line:129
    elif O00OOOO00O0O0O000 =="chapter_content":#line:130
        if len (sys .argv )<3 :#line:131
            print ("请提供章节ID")#line:132
            return #line:133
        O00O0OO00O0O0O0O0 =sys .argv [2 ]#line:134
        print (f"正在获取章节内容: {O00O0OO00O0O0O0O0}")#line:135
        OOOO0OOO00OOO0OOO =OOOO0OOOO0OOOOO00 .get_chapter_content (O00O0OO00O0O0O0O0 )#line:136
        if OOOO0OOO00OOO0OOO :#line:137
            print (json .dumps (OOOO0OOO00OOO0OOO ,ensure_ascii =False ,indent =2 ))#line:138
        else :#line:139
            print ("获取章节内容失败")#line:140
    elif O00OOOO00O0O0O000 =="download_full":#line:141
        if len (sys .argv )<4 :#line:142
            print ("请提供书籍ID和章节ID列表")#line:143
            return #line:144
        O00O0O0O00O0OOOO0 =sys .argv [2 ]#line:145
        O00O0OO00O0O0O0O0 =sys .argv [3 ]#line:146
        print (f"正在下载整本小说: {O00O0O0O00O0OOOO0}")#line:147
        OOOO0OOO00OOO0OOO =OOOO0OOOO0OOOOO00 .download_full_novel (O00O0O0O00O0OOOO0 ,O00O0OO00O0O0O0O0 )#line:148
        if OOOO0OOO00OOO0OOO :#line:149
            print (json .dumps (OOOO0OOO00OOO0OOO ,ensure_ascii =False ,indent =2 ))#line:150
        else :#line:151
            print ("下载整本小说失败")#line:152
    else :#line:153
        print (f"未知命令: {O00OOOO00O0O0O000}")#line:154
        print ("支持的命令: search, novel_info, book_details, chapter_content, download_full")#line:155
if __name__ =="__main__":#line:156
    main ()