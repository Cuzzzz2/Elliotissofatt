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
