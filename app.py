import streamlit as st
import numpy as np
from amplify import VariableGenerator, Model, FixstarsClient, solve
from datetime import timedelta
import math

#テキスト表示
st.title('荷物を均等に分けよう')
st.write('荷物の重さ、分ける数を入力してSQAを実行')

col1,col2= st.columns(2)

with col1:
    # 荷物を用意
    w = np.array([17.6, 19.0, 7.2, 5.1, 18.6, 11.6, 18.3, 13.0, 3.6, 0.4, 12.0, 16.6, 19.8, 9.6, 4.0, 12.0, 16.9, 17.8, 11.0, 8.2])
    W = sum(w)
    N = len(w)

    # 荷物の重さを表示★
    st.write('荷物の重さ')
    st.data_editor(w)

with col2:
    #置き場所の数★
    K = st.number_input('置き場所の数を入力',value = 3,step = 1)

# 変数を発行
gen = VariableGenerator()
x = gen.array('Binary', shape=(N, K))

# コスト関数
cost = 1/K * sum((sum(w[i]*x[i,k] for i in range(N)) - 1/K * sum(sum(w[i]*x[i,k] for i in range(N)) for k in range(K)))**2 for k in range(K))

# 罰金項
lam = 20
penalty = lam * sum((sum(x[i,k] for k in range(K)) -1 )**2 for i in range(N))

# モデル
model = Model(cost + penalty)

# ソルバーの設定
client = FixstarsClient()
client.token = 'AE/zqJVysWXe6iax5u0vmCips7tmGPdIK0i' # アクセストークンを入力
client.parameters.timeout = timedelta(milliseconds=1000)  # タイムアウト 1000 ミリ秒

# 実行ボタンを表示★
button = st.button('SQAを実行')

if button: #★
    # 結果の取得
    result = solve(model, client)
    if len(result) == 0:
        raise RuntimeError('At least one of the constraints is not satisfied.')

    sample_array = x.evaluate(result.best.values)
    
    #重さテーブルの平均
    Wu = 1/K * sum(w[i]*sum(sample_array[i][k] for k in range(K)) for i in range(N))

    #各場所での重さ合計、コスト（分散）、標準偏差
    values = []#各場所での重さの合計
    cost = 0
    for k in range(K):
        value = 0
        for i in range(N):
            value = value + sample_array[i][k] * w[i]
        values.append(value)
        cost = cost + (value - Wu)**2
    cost = 1/K * cost#コスト
    standard_deviation = math.sqrt(cost)#標準偏差

    col3,col4,col5= st.columns(3)

    with col3:
        st.metric('コスト',cost)
    
    with col4:
        st.metric('平均',Wu)
    
    with col5:
        st.metric('標準偏差',standard_deviation)

    # 各場所に対して置くべき荷物をリストにまとめる
    allocation = []  # 各場所ごとの荷物リストを格納する

    for k in range(K):
        place_items = []  # その場所に置く荷物
        for i in range(N):
            if sample_array[i][k] == 1:
                place_items.append(w[i])
        allocation.append(place_items)

    allocation = np.array(allocation, dtype=object)
    st.write('各場所に置くべき荷物')
    st.write(allocation)

    #罰金項のチェック
    print('count=', end='')
    for i in range(N):
        count = 0
        for k in range(K):
            count = int(count + sample_array[i][k]) #★
        print(f'{count}', end=',')
