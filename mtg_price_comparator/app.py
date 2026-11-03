import os
import re
import urllib.parse
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title='MTG 売却比較', page_icon='🃏', layout='wide', initial_sidebar_state='collapsed')
SITES = ['晴れる屋（買取）', 'カードラッシュ（買取）', 'メルカリ', 'Yahoo!フリマ']
DOMAINS = ['hareruyamtg.com', 'cardrush-mtg.jp', 'jp.mercari.com', 'paypayfleamarket.yahoo.co.jp']


def search_link(site, name):
    q = urllib.parse.quote(name.strip(), safe='')
    if site == SITES[0]:
        return 'https://www.hareruyamtg.com/ja/purchase/search'
    if site == SITES[1]:
        return 'https://www.cardrush-mtg.jp/page/79'
    if site == SITES[2]:
        return 'https://jp.mercari.com/search?keyword=' + q
    return 'https://paypayfleamarket.yahoo.co.jp/search/' + q


def search_api(query, domain, key):
    r = requests.post('https://google.serper.dev/search', headers={'X-API-KEY': key, 'Content-Type': 'application/json'}, json={'q': f'site:{domain} {query}', 'gl': 'jp', 'hl': 'ja', 'num': 10}, timeout=15)
    r.raise_for_status()
    return r.json().get('organic', [])


def extract_candidates(results):
    out = []
    for item in results:
        content = str(item.get('title', '')) + ' ' + str(item.get('snippet', ''))
        for match in re.finditer(r'(?<!\d)(\d{1,3}(?:,\d{3})+|\d{2,7})\s*円', content):
            amount = int(match.group(1).replace(',', ''))
            if 10 <= amount <= 10_000_000:
                out.append({'価格候補（円）': amount, '検索結果': item.get('title', ''), '根拠の抜粋': content[max(0, match.start()-35):match.end()+35], '参照URL': item.get('link', '')})
    return out


def net_amount(site, unit_price, quantity, fee_mercari, fee_yahoo, shipping, other_cost):
    gross = unit_price * quantity
    fee_rate = fee_mercari if site == SITES[2] else fee_yahoo if site == SITES[3] else 0
    fee = int((Decimal(gross) * Decimal(str(fee_rate)) / 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    shipping_cost = shipping if site in SITES[2:] else 0
    return gross, fee, shipping_cost, gross - fee - shipping_cost - other_cost


st.title('🃏 MTG 売却価格比較')
st.caption('iPhone・Mac・Windows対応のWebアプリ。価格候補は未確認データです。正確な査定額・成約価格の自動取得は保証しません。')

with st.expander('⚙️ 検索条件・手数料', expanded=True):
    name = st.text_input('カード名', '偏向はたき')
    edition = st.text_input('セット・版（任意）', placeholder='例：統率者マスターズ')
    c1, c2, c3 = st.columns(3)
    with c1:
        language = st.selectbox('言語', ['日本語', '英語', 'その他'])
    with c2:
        foil = st.selectbox('仕様', ['通常', 'Foil', '特殊Foil'])
    with c3:
        qty = st.number_input('枚数', min_value=1, max_value=10000, value=1)
    c4, c5 = st.columns(2)
    with c4:
        mercari_fee = st.number_input('メルカリ手数料率（%）', 0.0, 30.0, 10.0, 0.5)
        yahoo_fee = st.number_input('Yahoo!フリマ手数料率（%）', 0.0, 30.0, 5.0, 0.5)
    with c5:
        shipping = st.number_input('フリマ送料・取引合計（円）', 0, 100000, 210, 10)
        other_cost = st.number_input('その他の費用・取引合計（円）', 0, 100000, 0, 10, help='振込・梱包・買取店への発送など、各取引で発生する費用')
    try:
        secret_key = st.secrets.get('SERPER_API_KEY', '')
    except (FileNotFoundError, KeyError):
        secret_key = ''
    api_key = st.text_input('Serper APIキー（任意）', value=os.getenv('SERPER_API_KEY', secret_key), type='password', help='公開配置ではStreamlit Community CloudのSecretsに登録するのがおすすめです。')
    st.caption('手数料率・送料は仮の初期値です。ご自身の適用条件で変更してください。')

if not name.strip():
    st.warning('カード名を入力してください。')
    st.stop()

query = ' '.join(filter(None, [name.strip(), edition.strip(), language, 'foil' if foil != '通常' else '', '買取']))
st.subheader('① 4サイトの検索')
for site in SITES:
    st.link_button(f'🔎 {site}を開く', search_link(site, name), use_container_width=True)
st.caption('買取店リンクは検索入口です。サイト内でカード名を入力してください。')

st.subheader('② 公開検索結果から価格候補を取得')
if st.button('4サイトを自動検索', type='primary', use_container_width=True):
    if not api_key.strip():
        st.warning('自動検索にはSerper APIキーが必要です。下の価格比較はキーなしで利用できます。')
    else:
        found = {}
        with st.spinner('検索中…'):
            for site, domain in zip(SITES, DOMAINS):
                try:
                    found[site] = extract_candidates(search_api(query, domain, api_key))
                except requests.RequestException:
                    found[site] = []
                    st.warning(f'{site}：検索に失敗しました。API設定・接続を確認してください。')
        st.session_state['found'] = found
        st.session_state['found_query'] = query

if st.session_state.get('found_query') == query and 'found' in st.session_state:
    for site, items in st.session_state['found'].items():
        with st.expander(f'{site}：{len(items)}件の価格候補'):
            if items:
                st.dataframe(pd.DataFrame(items), hide_index=True, use_container_width=True, column_config={'参照URL': st.column_config.LinkColumn('参照URL')})
            else:
                st.info('候補なし（未取得）')
            st.caption('検索結果の文章に含まれる「円」を抽出した参考値です。別カード・販売価格・古い価格の可能性があります。')
elif 'found' in st.session_state:
    st.info('検索条件が変わりました。「4サイトを自動検索」を押して再取得してください。')

st.subheader('③ 確認済み価格で手取り比較')
st.caption('1枚あたりの確認済み価格を入力。0円は未確認として扱います。')
rows = []
for site in SITES:
    price = st.number_input(f'{site}（円／枚）', min_value=0, max_value=100_000_000, value=0, step=100, key=f'price_{site}')
    if price:
        gross, fee, post, net = net_amount(site, price, qty, mercari_fee, yahoo_fee, shipping, other_cost)
    else:
        gross = fee = post = net = None
    rows.append({'サイト': site, '単価（円）': price if price else None, '枚数': qty, '売却総額（円）': gross, '手数料（円）': fee, '送料（円）': post, 'その他費用（円）': other_cost if price else None, '手取り（円）': net, '検索リンク': search_link(site, name)})

df = pd.DataFrame(rows)
st.dataframe(df, hide_index=True, use_container_width=True, column_config={'検索リンク': st.column_config.LinkColumn('サイトを開く')})
valid = df.dropna(subset=['手取り（円）'])
if len(valid):
    best = valid.sort_values('手取り（円）', ascending=False).iloc[0]
    st.success(f'確認済み価格の中で最高：{best["サイト"]} ／ 手取り {int(best["手取り（円）"]):,} 円（{qty}枚合計）')
else:
    st.info('価格を入力すると比較結果を表示します。')

st.download_button('📥 比較結果をCSVで保存', df.to_csv(index=False).encode('utf-8-sig'), 'mtg_comparison.csv', 'text/csv', use_container_width=True)
st.caption('注意：自動検索はGoogle検索のスニペットを使用し、各サイトの買取・成約価格を直接取得しません。入力価格やAPIキーは永続保存されません。公開URLを他人と共有する場合は個人情報やキーの扱いに注意してください。')
