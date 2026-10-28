import math
import random
import pygame

# ------------------------------------------------------------
# 교육용 물리학 미사일 게임
# 실행 전: pip install pygame
# 실행: python physics_missile_game.py
# ------------------------------------------------------------

pygame.init()

WIDTH, HEIGHT = 1000, 650
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("물리학 미사일 발사 실험")
CLOCK = pygame.time.Clock()

FONT = pygame.font.SysFont("malgungothic", 22)
SMALL_FONT = pygame.font.SysFont("malgungothic", 17)
BIG_FONT = pygame.font.SysFont("malgungothic", 30)

# 화면/세계 설정
GROUND_Y = HEIGHT - 65
PIXELS_PER_METER = 3.0
GRAVITY = 9.81                   # m/s^2
AIR_DENSITY = 1.225              # kg/m^3
MISSILE_MASS = 8.0               # kg (교육용 가상 값)
DRAG_COEFFICIENT = 0.45          # 무차원 항력 계수
REFERENCE_AREA = 0.025           # m^2
LIFT_COEFFICIENT = 0.18          # 교육용 고정 양력 계수
THRUST_NEWTONS = 65.0            # N, 엔진 작동 중 추력
ENGINE_DURATION = 1.4            # s
TIME_STEP = 1 / 120              # 물리 계산 시간 간격
MAX_FLIGHT_TIME = 35.0

# 게임 상태
angle_degrees = 45
launch_speed = 55.0              # m/s
missile = None
target = None
score = 0
message = "각도와 초기 속도를 설정한 뒤 발사하세요."
flight_time = 0.0
trail = []
game_over = False


def new_target():
    """플레이어가 도달할 수 있도록 적당한 범위 안에 목표물을 생성한다."""
    x = random.uniform(170, 285) if score == 0 else random.uniform(145, 300)
    y = random.uniform(35, 125)
    return {"x": x, "y": y, "radius": 12}


def world_to_screen(x, y):
    sx = int(55 + x * PIXELS_PER_METER)
    sy = int(GROUND_Y - y * PIXELS_PER_METER)
    return sx, sy


def reset_missile():
    global missile, flight_time, trail, message
    angle = math.radians(angle_degrees)
    start_x = 8.0
    start_y = 3.0
    missile = {
        "x": start_x,
        "y": start_y,
        "vx": launch_speed * math.cos(angle),
        "vy": launch_speed * math.sin(angle),
        "mass": MISSILE_MASS,
        "t": 0.0,
        "active": True,
    }
    flight_time = 0.0
    trail = []
    update_physics.last_trail_t = -1.0
    message = "발사! 힘의 합력에 따라 궤적이 변합니다."


def draw_text(text, x, y, font=FONT, color=(25, 35, 50)):
    image = font.render(text, True, color)
    SCREEN.blit(image, (x, y))


def draw_scene():
    SCREEN.fill((220, 240, 255))

    # 구름
    for cx, cy in [(150, 95), (430, 65), (740, 110), (890, 55)]:
        pygame.draw.circle(SCREEN, (255, 255, 255), (cx, cy), 18)
        pygame.draw.circle(SCREEN, (255, 255, 255), (cx + 20, cy + 3), 23)
        pygame.draw.circle(SCREEN, (255, 255, 255), (cx + 42, cy), 16)

    # 지면
    pygame.draw.rect(SCREEN, (105, 178, 103), (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))
    pygame.draw.line(SCREEN, (55, 120, 63), (0, GROUND_Y), (WIDTH, GROUND_Y), 3)

    # 눈금
    for meters in range(0, 301, 20):
        x = int(55 + meters * PIXELS_PER_METER)
        if x < WIDTH:
            pygame.draw.line(SCREEN, (130, 155, 165), (x, GROUND_Y), (x, GROUND_Y + 8), 1)
            draw_text(str(meters), x - 10, GROUND_Y + 10, SMALL_FONT, (50, 70, 80))

    # 발사대
    base_x, base_y = world_to_screen(8, 0)
    pygame.draw.rect(SCREEN, (70, 75, 85), (base_x - 18, GROUND_Y - 14, 45, 14))
    pygame.draw.polygon(
        SCREEN, (75, 85, 100),
        [(base_x - 10, GROUND_Y - 14), (base_x + 2, GROUND_Y - 34),
         (base_x + 14, GROUND_Y - 14)]
    )

    # 미사일 비행 흔적
    if len(trail) > 1:
        points = [world_to_screen(x, y) for x, y in trail]
        pygame.draw.lines(SCREEN, (235, 115, 55), False, points, 2)

    # 목표물
    if target:
        tx, ty = world_to_screen(target["x"], target["y"])
        pygame.draw.circle(SCREEN, (210, 45, 50), (tx, ty), target["radius"])
        pygame.draw.circle(SCREEN, (255, 255, 255), (tx, ty), 5)
        pygame.draw.line(SCREEN, (210, 45, 50), (tx - 20, ty), (tx + 20, ty), 2)
        pygame.draw.line(SCREEN, (210, 45, 50), (tx, ty - 20), (tx, ty + 20), 2)

    # 미사일
    if missile:
        mx, my = world_to_screen(missile["x"], missile["y"])
        angle = math.atan2(missile["vy"], missile["vx"])
        length = 20
        nose = (mx + int(math.cos(angle) * length), my - int(math.sin(angle) * length))
        tail = (mx - int(math.cos(angle) * length * 0.55), my + int(math.sin(angle) * length * 0.55))
        pygame.draw.line(SCREEN, (50, 55, 65), tail, nose, 7)
        pygame.draw.circle(SCREEN, (255, 190, 65), tail, 4)

    # 정보 패널
    pygame.draw.rect(SCREEN, (255, 255, 255), (12, 12, 405, 166), border_radius=12)
    pygame.draw.rect(SCREEN, (140, 170, 190), (12, 12, 405, 166), 2, border_radius=12)
    draw_text("물리학 미사일 발사 실험", 25, 20, BIG_FONT)
    draw_text(f"점수: {score}     각도: {angle_degrees}°     초기 속도: {launch_speed:.0f} m/s", 25, 58, SMALL_FONT)
    draw_text(f"중력: {GRAVITY:.2f} m/s²   질량: {MISSILE_MASS:.1f} kg", 25, 84, SMALL_FONT)
    draw_text(f"추력: {THRUST_NEWTONS:.0f} N (처음 {ENGINE_DURATION:.1f}초)", 25, 108, SMALL_FONT)
    if missile and missile["active"]:
        speed = math.hypot(missile["vx"], missile["vy"])
        draw_text(f"비행 시간: {missile['t']:.2f} s   현재 속력: {speed:.1f} m/s", 25, 132, SMALL_FONT)
    else:
        draw_text("← / → 각도   ↑ / ↓ 속도   SPACE 발사", 25, 132, SMALL_FONT)

    # 안내 메시지
    pygame.draw.rect(SCREEN, (255, 255, 255), (12, HEIGHT - 38, WIDTH - 24, 28), border_radius=7)
    draw_text(message, 22, HEIGHT - 36, SMALL_FONT, (35, 55, 70))


def update_physics(dt):
    """추력, 중력, 항력, 양력을 합산해 뉴턴의 제2법칙으로 운동을 계산한다."""
    global message, score, target, missile, flight_time, trail

    if not missile or not missile["active"]:
        return

    x, y = missile["x"], missile["y"]
    vx, vy = missile["vx"], missile["vy"]
    speed = math.hypot(vx, vy)
    mass = missile["mass"]

    # 힘 1: 중력 (아래 방향)
    fx = 0.0
    fy = -mass * GRAVITY

    # 힘 2: 추력 (엔진 작동 중 미사일의 현재 진행 방향)
    if missile["t"] < ENGINE_DURATION and speed > 0.01:
        fx += THRUST_NEWTONS * vx / speed
        fy += THRUST_NEWTONS * vy / speed

    # 힘 3: 항력 Fd = 1/2 * rho * Cd * A * v^2
    # 항력은 항상 속도의 반대 방향으로 작용한다.
    if speed > 0.01:
        drag = 0.5 * AIR_DENSITY * DRAG_COEFFICIENT * REFERENCE_AREA * speed ** 2
        fx -= drag * vx / speed
        fy -= drag * vy / speed

        # 힘 4: 양력. 속도 방향에 수직인 방향으로 작용하는 단순화 모델
        # 실제 양력은 날개 형상, 받음각, 공기 밀도 등에 따라 달라진다.
        lift = 0.5 * AIR_DENSITY * speed ** 2 * REFERENCE_AREA * LIFT_COEFFICIENT
        fx += lift * (-vy / speed)
        fy += lift * (vx / speed)

    # 뉴턴의 제2법칙: a = F / m
    ax = fx / mass
    ay = fy / mass

    # 오일러 적분으로 속도와 위치 업데이트
    vx += ax * dt
    vy += ay * dt
    x += vx * dt
    y += vy * dt

    missile.update({"x": x, "y": y, "vx": vx, "vy": vy, "t": missile["t"] + dt})
    flight_time = missile["t"]

    # 궤적을 일정 간격으로 저장
    if len(trail) == 0 or missile["t"] - getattr(update_physics, "last_trail_t", -1) > 0.045:
        trail.append((x, y))
        update_physics.last_trail_t = missile["t"]

    # 명중 판정
    if target:
        distance = math.hypot(x - target["x"], y - target["y"])
        hit_radius = target["radius"] / PIXELS_PER_METER + 1.6
        if distance <= hit_radius:
            score += 1
            target = new_target()
            missile["active"] = False
            message = f"명중! 점수 {score}점. 새 목표물이 생성됐어요. SPACE를 눌러 다시 발사하세요."
            return

    # 지면 충돌 / 비행 시간 제한
    if y <= 0 or missile["t"] >= MAX_FLIGHT_TIME or x < 0 or x > 310:
        missile["active"] = False
        message = "비행 종료! 각도 또는 초기 속도를 바꿔 다시 시도하세요."


def main():
    global angle_degrees, launch_speed, target, missile, message, score

    target = new_target()
    running = True

    while running:
        # 일정한 물리 시간 간격으로 계산해 프레임 속도에 따른 차이를 줄인다.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_LEFT:
                    angle_degrees = max(5, angle_degrees - 2)
                    message = f"발사 각도: {angle_degrees}°"
                elif event.key == pygame.K_RIGHT:
                    angle_degrees = min(85, angle_degrees + 2)
                    message = f"발사 각도: {angle_degrees}°"
                elif event.key == pygame.K_UP:
                    launch_speed = min(100, launch_speed + 2)
                    message = f"초기 속도: {launch_speed:.0f} m/s"
                elif event.key == pygame.K_DOWN:
                    launch_speed = max(15, launch_speed - 2)
                    message = f"초기 속도: {launch_speed:.0f} m/s"
                elif event.key == pygame.K_SPACE:
                    if not missile or not missile["active"]:
                        reset_missile()
                elif event.key == pygame.K_r:
                    score = 0
                    target = new_target()
                    missile = None
                    message = "게임을 초기화했어요."

        # 프레임 지연 시 한 번에 너무 크게 움직이지 않도록 제한
        frame_dt = min(CLOCK.tick(60) / 1000.0, 0.04)
        accumulator = getattr(main, "accumulator", 0.0) + frame_dt
        while accumulator >= TIME_STEP:
            update_physics(TIME_STEP)
            accumulator -= TIME_STEP
        main.accumulator = accumulator

        draw_scene()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
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
