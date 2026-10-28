import math
import random

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st


# ==========================================
# 1. 페이지 설정
# ==========================================
st.set_page_config(
    page_title="물리학 미사일 발사 게임",
    page_icon="🚀",
    layout="wide"
)

st.title("🚀 물리학 미사일 발사 시뮬레이션")
st.write(
    "발사 각도와 초기 속도를 조절하고, "
    "물리학 법칙을 적용해 목표물을 명중시켜 보세요!"
)


# ==========================================
# 2. 물리학 상수
# ==========================================
GRAVITY = 9.81
AIR_DENSITY = 1.225
MISSILE_MASS = 8.0

DRAG_COEFFICIENT = 0.45
REFERENCE_AREA = 0.025
LIFT_COEFFICIENT = 0.18

THRUST = 65.0
ENGINE_DURATION = 1.4

TIME_STEP = 0.01
MAX_FLIGHT_TIME = 35.0


# ==========================================
# 3. 게임 상태 초기화
# ==========================================
if "score" not in st.session_state:
    st.session_state.score = 0

if "target_x" not in st.session_state:
    st.session_state.target_x = random.uniform(170, 250)

if "target_y" not in st.session_state:
    st.session_state.target_y = random.uniform(25, 85)

if "result" not in st.session_state:
    st.session_state.result = None


# ==========================================
# 4. 물리학 시뮬레이션
# ==========================================
def simulate_missile(angle_degrees, initial_speed, target_x, target_y):
    """
    중력, 추력, 항력, 양력을 적용해
    미사일의 위치와 속도를 계산한다.
    """

    angle = math.radians(angle_degrees)

    x = 8.0
    y = 3.0

    vx = initial_speed * math.cos(angle)
    vy = initial_speed * math.sin(angle)

    t = 0.0

    xs = [x]
    ys = [y]
    times = [t]
    speeds = [math.hypot(vx, vy)]

    hit = False
    hit_time = None

    while t < MAX_FLIGHT_TIME and y > 0 and x < 310:

        speed = math.hypot(vx, vy)

        # 합력 초기화
        fx = 0.0
        fy = -MISSILE_MASS * GRAVITY

        # ----------------------------------
        # 추력
        # ----------------------------------
        if t < ENGINE_DURATION and speed > 1e-8:
            fx += THRUST * vx / speed
            fy += THRUST * vy / speed

        # ----------------------------------
        # 항력
        # ----------------------------------
        if speed > 1e-8:
            drag = (
                0.5
                * AIR_DENSITY
                * DRAG_COEFFICIENT
                * REFERENCE_AREA
                * speed**2
            )

            fx -= drag * vx / speed
            fy -= drag * vy / speed

            # ----------------------------------
            # 양력
            # 진행 방향에 수직인 단순화된 양력
            # ----------------------------------
            lift = (
                0.5
                * AIR_DENSITY
                * speed**2
                * REFERENCE_AREA
                * LIFT_COEFFICIENT
            )

            fx += lift * (-vy / speed)
            fy += lift * (vx / speed)

        # ----------------------------------
        # 뉴턴의 운동 제2법칙
        # F = ma -> a = F/m
        # ----------------------------------
        ax = fx / MISSILE_MASS
        ay = fy / MISSILE_MASS

        # 속도 업데이트
        vx += ax * TIME_STEP
        vy += ay * TIME_STEP

        # 위치 업데이트
        x += vx * TIME_STEP
        y += vy * TIME_STEP

        t += TIME_STEP

        xs.append(x)
        ys.append(y)
        times.append(t)
        speeds.append(math.hypot(vx, vy))

        # ----------------------------------
        # 목표물 명중 판정
        # ----------------------------------
        distance = math.hypot(
            x - target_x,
            y - target_y
        )

        if distance <= 4.0:
            hit = True
            hit_time = t
            break

    return {
        "x": np.array(xs),
        "y": np.array(ys),
        "time": np.array(times),
        "speed": np.array(speeds),
        "hit": hit,
        "hit_time": hit_time,
        "angle": angle_degrees,
        "initial_speed": initial_speed
    }


# ==========================================
# 5. 게임 화면과 조작
# ==========================================
left, right = st.columns([1, 2])

with left:

    st.subheader("🎮 발사 설정")

    angle = st.slider(
        "발사 각도",
        min_value=5,
        max_value=85,
        value=45,
        step=1,
        format="%d°"
    )

    initial_speed = st.slider(
        "초기 속도",
        min_value=15,
        max_value=100,
        value=55,
        step=1,
        format="%d m/s"
    )

    st.metric("현재 점수", st.session_state.score)

    st.write(
        f"목표물 수평 거리: "
        f"{st.session_state.target_x:.1f} m"
    )

    st.write(
        f"목표물 높이: "
        f"{st.session_state.target_y:.1f} m"
    )

    fire_button = st.button(
        "🚀 미사일 발사",
        type="primary",
        use_container_width=True
    )

    new_target_button = st.button(
        "🎯 새 목표물 생성",
        use_container_width=True
    )

    reset_button = st.button(
        "🔄 게임 초기화",
        use_container_width=True
    )


# ==========================================
# 6. 버튼 동작
# ==========================================
if new_target_button:

    st.session_state.target_x = random.uniform(150, 270)
    st.session_state.target_y = random.uniform(20, 90)
    st.session_state.result = None

    st.rerun()


if reset_button:

    st.session_state.score = 0
    st.session_state.target_x = random.uniform(170, 250)
    st.session_state.target_y = random.uniform(25, 85)
    st.session_state.result = None

    st.rerun()


if fire_button:

    result = simulate_missile(
        angle,
        initial_speed,
        st.session_state.target_x,
        st.session_state.target_y
    )

    st.session_state.result = result

    if result["hit"]:

        st.session_state.score += 1

        # 명중하면 새로운 목표물 생성
        st.session_state.target_x = random.uniform(150, 270)
        st.session_state.target_y = random.uniform(20, 90)

        st.success(
            f"🎯 명중! 비행 시간: "
            f"{result['hit_time']:.2f}초"
        )

    else:

        st.warning(
            "목표물을 맞히지 못했습니다. "
            "각도 또는 초기 속도를 변경해 보세요."
        )


# ==========================================
# 7. 비행 궤적 그래프
# ==========================================
with right:

    st.subheader("📈 미사일 비행 궤적")

    fig, ax = plt.subplots(figsize=(10, 5))

    # 지면
    ax.axhline(
        y=0,
        color="green",
        linewidth=2,
        label="지면"
    )

    # 현재 목표물
    ax.scatter(
        [st.session_state.target_x],
        [st.session_state.target_y],
        color="red",
        marker="X",
        s=180,
        label="목표물"
    )

    result = st.session_state.result

    if result is not None:

        ax.plot(
            result["x"],
            result["y"],
            linewidth=2,
            label="미사일 궤적"
        )

        ax.scatter(
            result["x"][0],
            result["y"][0],
            marker="^",
            s=80,
            label="발사 위치"
        )

    else:

        ax.text(
            0.5,
            0.5,
            "발사 버튼을 눌러 미사일을 발사하세요!",
            transform=ax.transAxes,
            ha="center"
        )

    ax.set_xlim(0, 310)
    ax.set_ylim(0, 150)

    ax.set_xlabel("수평 거리 (m)")
    ax.set_ylabel("높이 (m)")
    ax.set_title("미사일의 포물선 운동")

    ax.grid(True, alpha=0.3)
    ax.legend()

    st.pyplot(fig)
    plt.close(fig)


# ==========================================
# 8. 비행 결과 분석
# ==========================================
result = st.session_state.result

if result is not None:

    st.subheader("📊 비행 결과")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "비행 시간",
        f"{result['time'][-1]:.2f}초"
    )

    col2.metric(
        "최고 높이",
        f"{np.max(result['y']):.2f} m"
    )

    col3.metric(
        "최대 수평 거리",
        f"{np.max(result['x']):.2f} m"
    )

    # 높이 그래프
    st.subheader("시간에 따른 높이 변화")

    height_fig, height_ax = plt.subplots()

    height_ax.plot(
        result["time"],
        result["y"]
    )

    height_ax.set_xlabel("시간 (초)")
    height_ax.set_ylabel("높이 (m)")
    height_ax.grid(True, alpha=0.3)

    st.pyplot(height_fig)
    plt.close(height_fig)

    # 속력 그래프
    st.subheader("시간에 따른 속력 변화")

    speed_fig, speed_ax = plt.subplots()

    speed_ax.plot(
        result["time"],
        result["speed"]
    )

    speed_ax.set_xlabel("시간 (초)")
    speed_ax.set_ylabel("속력 (m/s)")
    speed_ax.grid(True, alpha=0.3)

    st.pyplot(speed_fig)
    plt.close(speed_fig)


# ==========================================
# 9. 물리학 설명
# ==========================================
with st.expander("📚 게임에 적용된 물리학 원리"):

    st.markdown("""
    ### 중력

    미사일에 아래쪽으로 작용하는 힘입니다.

    `Fg = m × g`

    ### 추력

    엔진이 작동하는 동안 미사일의 진행 방향으로 작용합니다.

    ### 항력

    공기 저항으로 인해 발생하며 속도의 반대 방향으로 작용합니다.

    `Fd = 1/2 × ρ × Cd × A × v²`

    ### 양력

    이 게임에서는 미사일의 진행 방향에 수직으로 작용하는
    단순화된 양력 모델을 사용합니다.

    실제 양력은 받음각, 날개 모양, 공기 밀도 등에 따라 달라집니다.

    ### 뉴턴의 운동 제2법칙

    `F = ma`

    모든 힘을 합산해 가속도를 계산한 다음,
    속도와 위치를 짧은 시간 간격으로 갱신합니다.

    **주의:** 이 게임은 물리학 학습을 위한 단순화된 시뮬레이션이며,
    실제 미사일의 공기역학이나 유도·조종 성능을 재현하지 않습니다.
    """)
