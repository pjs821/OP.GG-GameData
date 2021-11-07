import requests # api 사용
import pandas as pd # 데이터프레임
import numpy as np
import pickle
import json
import time

api_key = 'RGAPI-f19547d5-e357-40de-9e15-c3cf2ec0b8f6' # api서비스사용을 위한 api_key

# 그랜드마스터티어의 소환사 정보를 가져오
GM_data = 'https://kr.api.riotgames.com/lol/league/v4/grandmasterleagues/by-queue/RANKED_SOLO_5x5?api_key=' + api_key 
r = requests.get(GM_data) # resquests모듈의 get함수를 통해 데이터 받아오기 

print("GM게임 데이터 받아오는중..")

if r.status_code == 429 : # 가져올수 있는 데이터 양이 초과됬을 경우 
    print('api cost full : infinite loop start')
    start_time = time.time() # 갱신 시간 체크를 위해 시작시간을 저장 

    while True : # 429error가 끝날 때까지 무한 루프
        if r.status_code == 429 :

            print('try 1 minute wait time')
            time.sleep(60) # 1분동안 기다린다. 
            print(r.status.code)

        elif r.status_code == 200 : # loop escape

            print('total wait time = ' , time.time() - start_time)
            print('recovery api cost')
            break # 갱신됬을 경우 무한반복 탈출 

            
GM_df = pd.DataFrame(r.json()) # 가져온 데이터를 데이터프레임형태로 저장 


GM_df.reset_index(inplace = True) # 인덱스정리
GM_entries_df = pd.DataFrame(dict(GM_df['entries'])).T # dict구조의 entries 컬럼 풀어주기
GM_df = pd.concat([GM_df , GM_entries_df] , axis = 1) # 열끼리 결합

GM_df = GM_df.drop(['index', 'queue' , 'name' , 'leagueId' , 'entries' , 'rank'] , axis = 1) # 필요없는 정보 정리

print("Success!!")
GM_df.to_csv("Process1.csv", encoding = "cp949", index = False) # 그랜드마스터티어의 유저데이터 csv





GM_df['accountId'] = None # summonerId를 이용하여 각 소환사의 accountId를 저장하기 위한 변수 
print("소환사ID 받아오는중..")
      
for i in range(len(GM_df)): # 소환사ID를 통해 accountID를 그랜드마스터 유저 데이터 정보에 추가 
    
    try :
        # summonerId를 통해 소환사 정보 조회
        SommonerId = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/' + GM_df['summonerId'].iloc[i] + '?api_key=' + api_key
        r = requests.get(SommonerId)

        while r.status_code == 429: # 429 : Rate limit exceeded
            print("status_code : ", r.status_code)
            print("time sleep.. 20seconds")
            time.sleep(20) # 갱신을 위해 20초간 슬립 
            SommonerId = 'https://kr.api.riotgames.com/lol/summoner/v4/summoners/' + GM_df['summonerId'].iloc[i] + '?api_key=' + api_key
            r = requests.get(SommonerId)

        AccountId = r.json()['accountId'] # 가져온 accountId데이터를 저장 
        GM_df.iloc[i, -1] = AccountId # 유저데이터에 accountId 데이터 추가


    except :
        print("failure")
        pass

print("Success!!")
GM_df.to_csv("Process2.csv", encoding = "cp949" ,index = False) # accountId를 추가한 유저데이터 csv





# accountId를 통해 gameId(matchId) 데이터를 받아와 데이터들을 연결 
print("소환사ID(accuntId)를 통해 게임ID 가져오는중 ..")
            
match_info_df = pd.DataFrame() # match데이터를 저장할 변수 

for i in range(len(GM_df)):
    # accountId를 통해 매치리스트를 받아온다.
    match = 'https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/' + GM_df['accountId'].iloc[i] + '?api_key=' + api_key
    r = requests.get(match)

    while r.status_code == 429 :
        print("loop location : ", i)
        print("time sleep.. 10seconds")
        time.sleep(10) # 갱신을 위해 10초 슬립 
        match = 'https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/' + GM_df['accountId'].iloc[i] + '?api_key=' + api_key
        r = requests.get(match)
                
    match_info_df = pd.concat([match_info_df , pd.DataFrame(r.json()['matches'])]) # 받아오는 매치데이터들을 데이터프레임형태로 연결 
 

match_info_df.duplicated(subset=['gameId']).value_counts() # 게임ID(matchID) 중복확인
match_info_df = match_info_df.drop_duplicates(subset=['gameId']) # 게임ID중복행 제거

print("Success!!")
match_info_df.to_csv("Process3.csv", encoding = "cp949", index = False) # 그랜드마스터티어 매치데이터(gameId) csv




print("게임ID를 통해 상세 정보 가져오는중..")

match_df = pd.DataFrame() # 실제 게임 내용을 저장할 변수

for i in range(len(match_info_df)):

    # gameId(matchId)를 이용한 게임데이터 추출
    in_game_match = 'https://kr.api.riotgames.com/lol/match/v4/matches/' + str(match_info_df['gameId'].iloc[i]) + '?api_key=' + api_key
    r = requests.get(in_game_match)

    if r.status_code == 200 : pass

    elif r.status_code == 429 :
        print('api cost full : infinite loop start')
        print('loop location : ' , i)
        start_time = time.time()

        while True : # 429error가 끝날 때까지 무한 루프
            if r.status_code == 429 :

                print('try 10 seconds wait time')
                time.sleep(10) # 갱신을 위해 10초간 슬립 

                r = requests.get(in_game_match)
                print(r.status_code)

            elif r.status_code == 200 : # loop escape

                print('total wait time = ' , time.time() - start_time)
                print('recovery api cost')
                break

    elif r.status_code == 503 : # service error
        print('service available error')
        start_time = time.time()

        while True :
            if r.status_code == 503 or r.status_code == 429 :

                print('try 10 seconds wait time')
                time.sleep(10) # 갱신을 위해 10초간 슬립 

                r = requests.get(in_game_match)
                print(r.status_code)

            elif r.status_code == 200 :
                print('total wait time = ' , time.time() - start_time)
                print('recovery api service')
                break
    elif r.status_code == 403 : # require api regenerate
        print('you need api renewal')
        print('break')
        break

    mat = pd.DataFrame(list(r.json().values()), index = list(r.json().keys())).T 
    match_df = pd.concat([match_df,mat])

match_df.dropna(thresh=2, inplace = True) # 결측값 제거
match_df.to_csv("GM_Game_Data(final).csv", encoding = "cp949" , index = False) # 중간 받아온 데이터 저장

print("Success!! , 파일저장 완료")



print("전처리 작업중..")        
match_df = match_df.loc[(match_df['gameVersion'] == '11.1.352.5559')&(match_df['gameMode']=='CLASSIC'), :] # 최신버전이면서 클래식게임만을 분리 
match_df.reset_index(inplace = True) # 인덱스 리셋

mat = pd.DataFrame() # 생성된 데이터프레임을 연결해 주기위한 변수
mat['lane'] = None # 역활군을 저장할 변수
mat['gameId'] = None # 게임ID를 저장할 변수 

count = 0 # 인덱스 제어를 위한 count 변수 


for i in range(len(match_df)) : # stats칼럼의 데이터를 얻기 위해 게임데이터 개수만큼 반복

    temp_lists = [] # 역활군 정보를 저장하기 위한 변수 
    temp_df = pd.DataFrame(match_df['participants'].iloc[i]) # 매치데이터에 있는 'participants'칼럼의 데이터들을 풀어서 변수에 저장    
    stats_df = pd.DataFrame(dict(temp_df['stats'])).T # participants 데이터 내의 딕셔너리형태로 있는 stats칼럼을 풀어서 저장
    
    for j in range(len(stats_df)) :

        role = temp_df['timeline'][j]['role'] # 플레이어별 역활군 저장 변수

        if role == 'DUO_SUPPORT' : # 서포터 
            temp = 'Support'
        elif role == 'DUO_CARRY' : # 원딜
            temp = 'AD CARRY'
        else : # 나머지 
            temp = temp_df['timeline'][j]['lane']

        temp_lists.append(temp) # 플레이어들의 역활군 정보를 리스트 형태로 저장

    if(len(set(temp_lists[:5])) == 5 & len(set(temp_lists[-5:])) == 5 ): # 각 팀의 5개의 역활군 정보가 맞을경우
        
        mat = pd.concat([mat, stats_df]) # 기본 데이터들을 연결
        
        for j in range(len(temp_lists)) : # 게임ID와 역활군 데이터 연결
            mat['gameId'].iloc[count] = match_df['gameId'].iloc[i]
            mat['lane'].iloc[count] = temp_lists[j]
            count += 1 # 인덱스 제어
        
        print(i ,"Success!!")
        

print("모든 작업을 완료했습니다.")
    

stats_df = mat.drop(['participantId','item0','item1','item2','item3','item4','item5','item6'], axis = 1) # 필요없는 정보 제거 
stats_df.reset_index(drop = True ,inplace = True) # 인덱스 정리 
stats_df.to_csv("Final_Game_Data.csv", encoding = "cp949" , index = False)        
        







