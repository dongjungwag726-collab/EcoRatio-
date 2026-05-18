import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 한글 폰트 설정
plt.rcParams['font.family'] = 'NanumGothic'
plt.rcParams['axes.unicode_minus'] = False
# -------------------------------------------------------
# 차종 데이터
# -------------------------------------------------------
car_data = {
    '아반떼 1.6 (가솔린)':  {'type': '오토',      'r': 13.0, 'gamma': 1.4,  'rc': 2.0, 'regen': 0,    'co2_per_liter': 2.31},
    'K5 2.0 (가솔린)':      {'type': '오토',      'r': 12.5, 'gamma': 1.4,  'rc': 2.0, 'regen': 0,    'co2_per_liter': 2.31},
    '포터 2 (디젤)':        {'type': '디젤',      'r': 17.0, 'gamma': 1.35, 'rc': 2.2, 'regen': 0,    'co2_per_liter': 2.64},
    '스타렉스 (디젤)':      {'type': '디젤',      'r': 16.5, 'gamma': 1.35, 'rc': 2.3, 'regen': 0,    'co2_per_liter': 2.64},
    '아반떼 하이브리드':    {'type': '하이브리드', 'r': 13.0, 'gamma': 1.4,  'rc': 2.0, 'regen': 0.25, 'co2_per_liter': 2.31},
    '그랜저 하이브리드':    {'type': '하이브리드', 'r': 13.5, 'gamma': 1.4,  'rc': 2.0, 'regen': 0.30, 'co2_per_liter': 2.31},
    '쏘나타 하이브리드':    {'type': '하이브리드', 'r': 13.0, 'gamma': 1.4,  'rc': 2.0, 'regen': 0.28, 'co2_per_liter': 2.31},
    '테슬라 모델 3':        {'type': '전기차',    'r': None, 'gamma': None,  'rc': None,'regen': 0,    'co2_per_liter': 0},
    '현대 아이오닉 6':      {'type': '전기차',    'r': None, 'gamma': None,  'rc': None,'regen': 0,    'co2_per_liter': 0},
    '기아 EV6':             {'type': '전기차',    'r': None, 'gamma': None,  'rc': None,'regen': 0,    'co2_per_liter': 0},
}

ev_efficiency = {
    '테슬라 모델 3':   0.88,
    '현대 아이오닉 6': 0.87,
    '기아 EV6':        0.86,
}

type_color = {
    '오토':      '#4C9BE8',
    '디젤':      '#E84C4C',
    '하이브리드': '#F5A623',
    '전기차':    '#4CE87C',
}

type_emoji = {
    '오토':      '⛽',
    '디젤':      '🛢️',
    '하이브리드': '⚡⛽',
    '전기차':    '⚡',
}

# -------------------------------------------------------
# 계산 함수
# -------------------------------------------------------
def calc_efficiency(car_name):
    d = car_data[car_name]
    if d['type'] == '전기차':
        return ev_efficiency.get(car_name, 0.87)
    elif d['type'] == '오토':
        return 1 - (1 / d['r'] ** (d['gamma'] - 1))
    elif d['type'] == '디젤':
        return 1 - (1 / d['r'] ** (d['gamma'] - 1)) * \
               ((d['rc'] ** d['gamma'] - 1) / (d['gamma'] * (d['rc'] - 1)))
    else:
        eta_e = 1 - (1 / d['r'] ** (d['gamma'] - 1))
        return eta_e + (1 - eta_e) * d['regen']

def calc_co2(car_name, dist):
    d = car_data[car_name]
    if d['type'] == '전기차':
        return dist * 0.18 * 0.459
    else:
        eta  = calc_efficiency(car_name)
        kmpl = eta / 0.30 * 15
        return (dist / kmpl) * d['co2_per_liter']

def calc_pv(car_name):
    d = car_data[car_name]
    if d['type'] == '전기차':
        return None
    r, gamma, rc = d['r'], d['gamma'], d['rc']
    V1, P1 = 1.0, 1.0
    V2 = V1 / r
    P2 = P1 * (V1 / V2) ** gamma
    if d['type'] in ('오토', '하이브리드'):
        P3, V3 = P2 * 4.0, V2
        P4 = P3 * (V3 / V1) ** gamma
        V_12 = np.linspace(V1, V2, 100); P_12 = P1 * (V1 / V_12) ** gamma
        V_23, P_23 = np.array([V2, V2]), np.array([P2, P3])
        V_34 = np.linspace(V2, V1, 100); P_34 = P3 * (V3 / V_34) ** gamma
        V_41, P_41 = np.array([V1, V1]), np.array([P4, P1])
    else:
        P3, V3 = P2, V2 * rc
        P4 = P3 * (V3 / V1) ** gamma
        V_12 = np.linspace(V1, V2, 100); P_12 = P1 * (V1 / V_12) ** gamma
        V_23, P_23 = np.linspace(V2, V3, 100), np.full(100, P2)
        V_34 = np.linspace(V3, V1, 100); P_34 = P3 * (V3 / V_34) ** gamma
        V_41, P_41 = np.array([V1, V1]), np.array([P4, P1])
    return {
        'curves': [(V_12, P_12, 'b'), (V_23, P_23, 'r'),
                   (V_34, P_34, 'g'), (V_41, P_41, 'k')],
        'states': ([V1, V2, V3, V1], [P1, P2, P3, P4])
    }

# -------------------------------------------------------
# 첫 화면: 타이틀 + 차량 선택 + 비교 버튼
# -------------------------------------------------------
st.title('🚗 어떤 차가 더 효율적일까?')
st.markdown('차량 두 개를 선택하고 **비교하기** 버튼을 눌러보세요.')

st.divider()

col_a, col_b = st.columns(2)
with col_a:
    car1_name = st.selectbox('🚘 차량 1', list(car_data.keys()), index=0)
with col_b:
    car2_name = st.selectbox('🚘 차량 2', list(car_data.keys()), index=7)

distance = st.number_input('주행 거리 (km)', min_value=10, max_value=1000, value=100, step=10)

compare_btn = st.button('🔍 비교하기', use_container_width=True, type='primary')

# -------------------------------------------------------
# 비교 버튼 클릭 후 결과 화면
# -------------------------------------------------------
if compare_btn:
    eta1 = calc_efficiency(car1_name)
    eta2 = calc_efficiency(car2_name)
    co2_1 = calc_co2(car1_name, distance)
    co2_2 = calc_co2(car2_name, distance)
    winner = car1_name if eta1 >= eta2 else car2_name
    winner_eta = max(eta1, eta2)

    st.divider()

    # ---- 핵심 결과: 크게 ----
    st.markdown(f'## 🏆 {winner} 이 더 효율적입니다!')

    col1, col2 = st.columns(2)

    with col1:
        d1 = car_data[car1_name]
        st.markdown(f"### {type_emoji[d1['type']]} {car1_name}")
        st.markdown(f"<h1 style='color:{type_color[d1['type']]};'>{eta1*100:.1f}%</h1>", unsafe_allow_html=True)
        st.markdown(f"**CO₂ {distance}km 기준:** {co2_1:.2f} kg")
        st.markdown(f"*{d1['type']}*")

    with col2:
        d2 = car_data[car2_name]
        st.markdown(f"### {type_emoji[d2['type']]} {car2_name}")
        st.markdown(f"<h1 style='color:{type_color[d2['type']]};'>{eta2*100:.1f}%</h1>", unsafe_allow_html=True)
        st.markdown(f"**CO₂ {distance}km 기준:** {co2_2:.2f} kg")
        st.markdown(f"*{d2['type']}*")

    # 효율 차이 강조
    st.info(f'📊 열효율 차이 **{abs(eta2-eta1)*100:.1f}%p** | CO₂ 절감량 **{abs(co2_1-co2_2):.2f}kg** ({distance}km 기준)')

    st.divider()

    # ---- 상세 분석: 탭 ----
    st.markdown('#### 📂 상세 분석')
    tab1, tab2, tab3 = st.tabs(['📊 효율 비교 그래프', '📈 PV 선도', '📋 공식 설명'])

    with tab1:
        # 두 차 막대 그래프
        fig, (ax_eta, ax_co2) = plt.subplots(1, 2, figsize=(10, 4))

        colors = [type_color[car_data[car1_name]['type']],
                  type_color[car_data[car2_name]['type']]]

        bars = ax_eta.bar([car1_name, car2_name], [eta1*100, eta2*100],
                          color=colors, width=0.4)
        for bar, val in zip(bars, [eta1*100, eta2*100]):
            ax_eta.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 0.5,
                        f'{val:.1f}%', ha='center', fontsize=12, fontweight='bold')
        ax_eta.set_ylabel('열효율 (%)')
        ax_eta.set_title('열효율 비교')
        ax_eta.set_ylim(0, 100)
        ax_eta.grid(axis='y', alpha=0.3)

        bars2 = ax_co2.bar([car1_name, car2_name], [co2_1, co2_2],
                           color=colors, width=0.4)
        for bar, val in zip(bars2, [co2_1, co2_2]):
            ax_co2.text(bar.get_x() + bar.get_width()/2,
                        bar.get_height() + 0.01,
                        f'{val:.2f}kg', ha='center', fontsize=12, fontweight='bold')
        ax_co2.set_ylabel('CO₂ 배출량 (kg)')
        ax_co2.set_title(f'CO₂ 배출량 ({distance}km)')
        ax_co2.grid(axis='y', alpha=0.3)

        plt.tight_layout()
        st.pyplot(fig)

        # 전체 차종 비교
        st.markdown('**전체 차종 열효율 비교**')
        all_names  = list(car_data.keys())
        all_etas   = [calc_efficiency(n)*100 for n in all_names]
        all_colors = [type_color[car_data[n]['type']] for n in all_names]

        fig2, ax2 = plt.subplots(figsize=(10, 4))
        bars_all = ax2.bar(all_names, all_etas, color=all_colors)
        for bar, val in zip(bars_all, all_etas):
            ax2.text(bar.get_x() + bar.get_width()/2,
                     bar.get_height() + 0.3,
                     f'{val:.1f}%', ha='center', fontsize=8)
        ax2.set_ylim(0, 100)
        ax2.set_ylabel('열효율 (%)')
        ax2.set_title('전체 차종 열효율')
        ax2.tick_params(axis='x', rotation=20)
        ax2.grid(axis='y', alpha=0.3)

        from matplotlib.patches import Patch
        ax2.legend(handles=[Patch(facecolor=c, label=t) for t, c in type_color.items()],
                   loc='upper left')
        st.pyplot(fig2)

    with tab2:
        pv1 = calc_pv(car1_name)
        pv2 = calc_pv(car2_name)
        labels_p = ['① 단열 압축', '② 열 공급', '③ 단열 팽창', '④ 열 방출']

        if pv1 and pv2:
            fig3, (ax3, ax4) = plt.subplots(1, 2, figsize=(12, 5))
            for ax, pv, name in [(ax3, pv1, car1_name), (ax4, pv2, car2_name)]:
                for (V, P, c), label in zip(pv['curves'], labels_p):
                    ax.plot(V, P, color=c, linewidth=2, label=label)
                sv, sp = pv['states']
                for v, p, lbl in zip(sv, sp, ['1','2','3','4']):
                    ax.plot(v, p, 'ko', markersize=7)
                    ax.annotate(f'  {lbl}', (v, p), fontsize=10)
                ax.set_xlabel('부피 V'); ax.set_ylabel('압력 P')
                ax.set_title(f'{name}  |  열효율 {calc_efficiency(name)*100:.1f}%')
                ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
            st.pyplot(fig3)
        elif pv1:
            fig3, ax3 = plt.subplots(figsize=(7, 5))
            for (V, P, c), label in zip(pv1['curves'], labels_p):
                ax3.plot(V, P, color=c, linewidth=2, label=label)
            sv, sp = pv1['states']
            for v, p, lbl in zip(sv, sp, ['1','2','3','4']):
                ax3.plot(v, p, 'ko', markersize=7)
                ax3.annotate(f'  {lbl}', (v, p), fontsize=10)
            ax3.set_title(f'{car1_name} PV 선도')
            ax3.legend(); ax3.grid(True, alpha=0.3)
            st.pyplot(fig3)
            st.info(f'⚡ {car2_name}은 전기차로 PV 사이클이 없습니다.')
        else:
            st.info('⚡ 두 차량 모두 전기차입니다.')

    with tab3:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('**오토 사이클**')
            st.markdown(r'$$\eta = 1 - \frac{1}{r^{\,\gamma-1}}$$')
        with col2:
            st.markdown('**디젤 사이클**')
            st.markdown(r'$$\eta = 1 - \frac{1}{r^{\,\gamma-1}} \cdot \frac{r_c^{\,\gamma}-1}{\gamma(r_c-1)}$$')
        with col3:
            st.markdown('**하이브리드**')
            st.markdown(r'$$\eta = \eta_{engine} + (1-\eta_{engine}) \times \eta_{regen}$$')

    # 출처
    st.divider()
    st.markdown('### 📚 데이터 출처')
    st.markdown('''
| 항목 | 출처 | 링크 |
|---|---|---|
| 아반떼 · 그랜저 · 아이오닉 사양 | 현대자동차 공식 홈페이지 | [🔗 hyundai.com](https://www.hyundai.com/kr/ko/e/all-vehicles) |
| K5 · EV6 사양 | 기아자동차 공식 홈페이지 | [🔗 kia.com](https://www.kia.com/kr/vehicles/ev) |
| 테슬라 모델3 효율 | 테슬라 공식 홈페이지 | [🔗 tesla.com](https://www.tesla.com/ko_KR/model3) |
| 전기차 탄소 계수 (0.459 kg/kWh) | 한국에너지공단 | [🔗 energy.or.kr](https://www.energy.or.kr) |
| CO₂ 배출계수 | 환경부 | [🔗 me.go.kr](https://www.me.go.kr) |
| 하이브리드 회생제동 효율 | 한국자동차연구원 | [🔗 katech.re.kr](https://www.katech.re.kr) |
    ''')
    st.caption('※ 본 시뮬레이터는 열역학 이론 모델 기반으로, 실제 차량 성능과 다소 차이가 있을 수 있습니다.')
