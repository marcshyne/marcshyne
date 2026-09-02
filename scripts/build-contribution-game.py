from collections import deque
from pathlib import Path
import random


COLS, ROWS = 40, 8
CELL, PITCH = 22, 28
X0, Y0 = 40, 64
STEP_SECONDS, TOTAL_SECONDS = 0.08, 48
FOOD_COUNT, GROWTH_PER_FOOD, POINTS_PER_FOOD = 70, 3, 250


def fmt(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".")


def opacity_animation(start: float, end: float) -> str:
    if start == 0:
        return (
            f'<animate attributeName="opacity" values="1;0;0;1" '
            f'keyTimes="0;{fmt(end / TOTAL_SECONDS)};.999;1" '
            f'calcMode="discrete" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>'
        )
    return (
        f'<animate attributeName="opacity" values="0;1;0;0" '
        f'keyTimes="0;{fmt(start / TOTAL_SECONDS)};{fmt(end / TOTAL_SECONDS)};1" '
        f'calcMode="discrete" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>'
    )


def randomized_cycle(rng):
    coarse_cols, coarse_rows = COLS // 2, ROWS // 2
    stack, seen, tree = [(rng.randrange(coarse_cols), rng.randrange(coarse_rows))], set(), []
    while stack:
        column, row = stack[-1]
        seen.add((column, row))
        choices = [
            candidate for candidate in ((column + 1, row), (column - 1, row), (column, row + 1), (column, row - 1))
            if 0 <= candidate[0] < coarse_cols and 0 <= candidate[1] < coarse_rows and candidate not in seen
        ]
        if choices:
            neighbor = rng.choice(choices)
            tree.append(((column, row), neighbor))
            stack.append(neighbor)
        else:
            stack.pop()

    edges = set()
    for column in range(coarse_cols):
        for row in range(coarse_rows):
            top_left, top_right = (2 * column, 2 * row), (2 * column + 1, 2 * row)
            bottom_right, bottom_left = (2 * column + 1, 2 * row + 1), (2 * column, 2 * row + 1)
            edges.update(frozenset(pair) for pair in (
                (top_left, top_right), (top_right, bottom_right),
                (bottom_right, bottom_left), (bottom_left, top_left),
            ))

    for (left_column, top_row), (right_column, bottom_row) in tree:
        if left_column != right_column:
            column, row = min(left_column, right_column), top_row
            old = (((2 * column + 1, 2 * row), (2 * column + 1, 2 * row + 1)),
                   ((2 * column + 2, 2 * row), (2 * column + 2, 2 * row + 1)))
            new = (((2 * column + 1, 2 * row), (2 * column + 2, 2 * row)),
                   ((2 * column + 1, 2 * row + 1), (2 * column + 2, 2 * row + 1)))
        else:
            column, row = left_column, min(top_row, bottom_row)
            old = (((2 * column, 2 * row + 1), (2 * column + 1, 2 * row + 1)),
                   ((2 * column, 2 * row + 2), (2 * column + 1, 2 * row + 2)))
            new = (((2 * column, 2 * row + 1), (2 * column, 2 * row + 2)),
                   ((2 * column + 1, 2 * row + 1), (2 * column + 1, 2 * row + 2)))
        edges.difference_update(frozenset(pair) for pair in old)
        edges.update(frozenset(pair) for pair in new)

    cells = [(column, row) for column in range(COLS) for row in range(ROWS)]
    neighbors = {cell: [] for cell in cells}
    for edge in edges:
        left, right = tuple(edge)
        neighbors[left].append(right)
        neighbors[right].append(left)
    assert len(tree) == coarse_cols * coarse_rows - 1 and all(len(value) == 2 for value in neighbors.values())
    start = rng.choice(cells)
    previous, current = None, start
    result = []
    while current not in result:
        result.append(current)
        options = neighbors[current]
        next_cell = rng.choice(options) if previous is None else (options[0] if options[0] != previous else options[1])
        previous, current = current, next_cell

    directions = [(bx - ax, by - ay) for (ax, ay), (bx, by) in zip(result, result[1:] + result[:1])]
    turns = sum(left != right for left, right in zip(directions, directions[1:] + directions[:1]))
    assert len(result) == COLS * ROWS and current == start and turns > 70
    return result


def build_game():
    rng = random.Random(4_204_204)
    cycle = randomized_cycle(rng)
    start_index = rng.randrange(len(cycle))
    body = deque(cycle[(start_index - offset) % len(cycle)] for offset in range(8))
    route, states, food_steps = [body[0]], [list(body)], set()
    cycle_index, growth_debt = start_index, 0

    for _ in range(FOOD_COUNT):
        distance = rng.randint(3, 8)
        target = cycle[(cycle_index + distance) % len(cycle)]
        while target in body:
            distance += 1
            target = cycle[(cycle_index + distance) % len(cycle)]
        for move in range(1, distance + 1):
            cycle_index = (cycle_index + 1) % len(cycle)
            head = cycle[cycle_index]
            assert head not in body
            body.appendleft(head)
            if move == distance:
                food_steps.add(len(route))
                growth_debt += GROWTH_PER_FOOD
            if growth_debt:
                growth_debt -= 1
            else:
                body.pop()
            route.append(head)
            states.append(list(body))

    while growth_debt:
        cycle_index = (cycle_index + 1) % len(cycle)
        head = cycle[cycle_index]
        assert head not in body
        body.appendleft(head)
        growth_debt -= 1
        route.append(head)
        states.append(list(body))

    for _ in range(len(cycle)):
        head, neck = body[0], body[1]
        incoming = (head[0] - neck[0], head[1] - neck[1])
        next_on_cycle = cycle[(cycle_index + 1) % len(cycle)]
        candidates = []
        for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            target = (head[0] + dx, head[1] + dy)
            if target in body and target not in (neck, body[-1], next_on_cycle) and incoming[0] * dx + incoming[1] * dy == 0:
                candidates.append(target)
        if candidates:
            collision = rng.choice(candidates)
            body.appendleft(collision)
            body.pop()
            route.append(collision)
            states.append(list(body))
            break
        cycle_index = (cycle_index + 1) % len(cycle)
        next_head = cycle[cycle_index]
        assert next_head not in body
        body.appendleft(next_head)
        body.pop()
        route.append(next_head)
        states.append(list(body))
    else:
        raise AssertionError("no natural self-collision opportunity")

    assert all(abs(ax - bx) + abs(ay - by) == 1 for (ax, ay), (bx, by) in zip(route, route[1:]))
    assert route[-1] in states[-2][1:-1]
    assert len(food_steps) == FOOD_COUNT and len(states[-2]) == 8 + FOOD_COUNT * GROWTH_PER_FOOD
    assert (len(route) - 1) * STEP_SECONDS < TOTAL_SECONDS - 7
    return route, food_steps, states


def build_svg() -> str:
    route, food_steps, states = build_game()
    collision_time = (len(route) - 1) * STEP_SECONDS
    overlay_start = collision_time + 0.65
    overlay_end = TOTAL_SECONDS - 1.0
    game_times = f"0;{fmt(overlay_start / TOTAL_SECONDS)};{fmt((overlay_start + .25) / TOTAL_SECONDS)};{fmt(overlay_end / TOTAL_SECONDS)};1"
    step_times = ";".join(fmt(i * STEP_SECONDS / TOTAL_SECONDS) for i in range(len(route))) + ";1"

    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="360" viewBox="0 0 1200 360" role="img" aria-labelledby="title desc" data-step-snake="true">',
        '  <title id="title">Marc Shyne contribution snake</title>',
        f'  <desc id="desc">A snake starts at a random cell, chases {FOOD_COUNT} random targets through an irregular grid route, grows to {8 + FOOD_COUNT * GROWTH_PER_FOOD} cells, shakes after a real tail collision, shows Game Over, and restarts.</desc>',
        '  <defs>',
        '    <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#07111f"/><stop offset="1" stop-color="#02060d"/></linearGradient>',
        '    <linearGradient id="body" x1="0" x2="1"><stop stop-color="#075cff"/><stop offset=".58" stop-color="#00aeef"/><stop offset="1" stop-color="#93f4ff"/></linearGradient>',
        '    <radialGradient id="food"><stop stop-color="#ffffff"/><stop offset=".35" stop-color="#7debff"/><stop offset="1" stop-color="#075cff"/></radialGradient>',
        '    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><rect width="22" height="22" rx="5" fill="#08111d" stroke="#132640" stroke-width="1"/></pattern>',
        '    <filter id="glow"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '    <filter id="softGlow"><feGaussianBlur stdDeviation="7" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
        '  </defs>',
        '  <rect width="1200" height="360" rx="24" fill="#02060d"/>',
        '  <rect x="24" y="16" width="1152" height="320" rx="20" fill="url(#panel)" stroke="#132640"/>',
        '  <text x="40" y="42" fill="#7debff" font-family="Arial,Helvetica,sans-serif" font-size="13" font-weight="800" letter-spacing="3">MARC SHYNE // CONTRIBUTION SNAKE</text>',
        f'  <text x="1160" y="42" text-anchor="end" fill="#49627f" font-family="Arial,Helvetica,sans-serif" font-size="12" font-weight="700" letter-spacing="2">LEVEL 08 // {int(STEP_SECONDS * 1000)} MS</text>',
        '  <rect x="32" y="56" width="1136" height="224" rx="10" fill="url(#grid)" stroke="#173253"/>',
        '  <rect x="32" y="56" width="1136" height="224" rx="10" fill="none" stroke="#00aeef" opacity=".18"><animate attributeName="opacity" values=".12;.3;.12" dur="4s" repeatCount="indefinite"/></rect>',
        '  <g aria-label="Food appears one cell at a time">',
    ]

    foods = sorted(food_steps)
    for number, step in enumerate(foods, 1):
        previous = 0 if number == 1 else foods[number - 2] * STEP_SECONDS
        eaten = step * STEP_SECONDS
        column, row = route[step]
        x, y = X0 + column * PITCH + CELL / 2, Y0 + row * PITCH + CELL / 2
        lines.extend([
            f'    <g id="food-{number}" opacity="0" transform="translate({x:g} {y:g})" filter="url(#glow)">',
            '      <rect x="-7" y="-7" width="14" height="14" rx="4" fill="url(#food)" transform="rotate(45)"/>',
            '      <circle r="11" fill="none" stroke="#7debff" opacity=".35"/>',
            f'      {opacity_animation(previous, eaten)}',
            '    </g>',
        ])
    lines.append('  </g>')

    max_length = max(map(len, states))
    shake_times = [0, collision_time] + [collision_time + offset for offset in (.08, .16, .24, .32, .4, .48, .58)] + [TOTAL_SECONDS]
    shake_values = ["0 0", "0 0", "-5 1", "5 -2", "-4 2", "4 -1", "-2 -2", "2 1", "0 0", "0 0"]
    lines.extend([
        '  <g aria-label="Snake" data-collision-shake="true">',
        f'    <animateTransform attributeName="transform" type="translate" values="{";".join(shake_values)}" keyTimes="{";".join(fmt(value / TOTAL_SECONDS) for value in shake_times)}" calcMode="discrete" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>',
        '    <g aria-label="Snake body" filter="url(#glow)">',
    ])
    body_fade_times = f"0;{fmt(collision_time / TOTAL_SECONDS)};{fmt((collision_time + .3) / TOTAL_SECONDS)};{fmt((overlay_start + .2) / TOTAL_SECONDS)};{fmt(overlay_end / TOTAL_SECONDS)};1"
    lines.append(f'    <animate attributeName="opacity" values="1;1;.55;.22;.22;1" keyTimes="{body_fade_times}" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>')
    for segment in range(max_length - 1, 0, -1):
        transforms = []
        for state in states:
            if segment < len(state):
                column, row = state[segment]
                transforms.append(f"{X0 + column * PITCH} {Y0 + row * PITCH}")
            else:
                transforms.append("-80 -80")
        transforms.append(transforms[-1])
        lines.extend([
            f'    <rect width="{CELL}" height="{CELL}" rx="6" fill="url(#body)" opacity="{max(.38, 1 - segment * .008):.3f}">',
            f'      <animateTransform attributeName="transform" type="translate" values="{";".join(transforms)}" keyTimes="{step_times}" calcMode="discrete" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>',
            '    </rect>',
        ])
    lines.append('    </g>')

    transforms, rotations = [], []
    last_direction = (1, 0)
    rotation_map = {(1, 0): 0, (0, 1): 90, (-1, 0): 180, (0, -1): 270}
    for index, (column, row) in enumerate(route):
        if index:
            previous = route[index - 1]
            last_direction = (column - previous[0], row - previous[1])
        transforms.append(f"{X0 + column * PITCH} {Y0 + row * PITCH}")
        rotations.append(f"{rotation_map[last_direction]} {CELL / 2:g} {CELL / 2:g}")
    transforms.append(transforms[-1])
    rotations.append(rotations[-1])
    lines.extend([
        '    <g aria-label="Snake head" filter="url(#softGlow)">',
        f'    <animateTransform attributeName="transform" type="translate" values="{";".join(transforms)}" keyTimes="{step_times}" calcMode="discrete" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>',
        f'    <rect width="{CELL}" height="{CELL}" rx="7" fill="#d8fbff" stroke="#075cff" stroke-width="3"/>',
        '    <g>',
        f'      <animateTransform attributeName="transform" type="rotate" values="{";".join(rotations)}" keyTimes="{step_times}" calcMode="discrete" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>',
        '      <circle cx="16" cy="7" r="2" fill="#02060d"/><circle cx="16" cy="15" r="2" fill="#02060d"/>',
        '    </g>',
        f'    <animate attributeName="opacity" values="1;1;.25;.25;1" keyTimes="0;{fmt(collision_time / TOTAL_SECONDS)};{fmt((collision_time + .5) / TOTAL_SECONDS)};{fmt(overlay_end / TOTAL_SECONDS)};1" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>',
        '    </g>',
        '  </g>',
    ])

    collision_column, collision_row = route[-1]
    cx = X0 + collision_column * PITCH + CELL / 2
    cy = Y0 + collision_row * PITCH + CELL / 2
    burst_start = collision_time / TOTAL_SECONDS
    burst_end = (collision_time + .65) / TOTAL_SECONDS
    lines.extend([
        f'  <g transform="translate({cx:g} {cy:g})" opacity="0" filter="url(#softGlow)">',
        f'    <circle r="12" fill="none" stroke="#7debff" stroke-width="4"><animate attributeName="r" values="12;12;70;70;12" keyTimes="0;{fmt(burst_start)};{fmt(burst_end)};.999;1" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/></circle>',
        '    <path d="M-34 0H34M0-34V34M-24-24L24 24M24-24L-24 24" stroke="#eafcff" stroke-width="3"/>',
        f'    <animate attributeName="opacity" values="0;1;0;0" keyTimes="0;{fmt(burst_start)};{fmt(burst_end)};1" calcMode="discrete" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>',
        '  </g>',
        '  <g aria-label="Live score" font-family="Arial,Helvetica,sans-serif" font-size="12" font-weight="800" letter-spacing="2">',
    ])

    score_marks = [(0, 0)] + [(step * STEP_SECONDS, index * POINTS_PER_FOOD) for index, step in enumerate(foods, 1) if index % 10 == 0]
    if score_marks[-1][1] != len(foods) * POINTS_PER_FOOD:
        score_marks.append((foods[-1] * STEP_SECONDS, len(foods) * POINTS_PER_FOOD))
    for index, (start, score) in enumerate(score_marks):
        end = score_marks[index + 1][0] if index + 1 < len(score_marks) else overlay_start
        lines.extend([
            f'    <text x="1160" y="318" text-anchor="end" fill="#7debff" opacity="0">SCORE {score:06d}',
            f'      {opacity_animation(start, end)}',
            '    </text>',
        ])
    lines.extend([
        '  </g>',
        '  <text x="40" y="318" fill="#49627f" font-family="Arial,Helvetica,sans-serif" font-size="12" font-weight="700" letter-spacing="2">BOARD 40×8 // ONE FOOD // GRID-LOCKED MOTION</text>',
        '  <g aria-label="Game over results" opacity="0">',
        '    <rect x="0" y="0" width="1200" height="360" rx="24" fill="#01040a" opacity=".82"/>',
        '    <rect x="292" y="72" width="616" height="224" rx="18" fill="#050c16" stroke="#155eef" stroke-width="2"/>',
        '    <rect x="304" y="84" width="592" height="200" rx="12" fill="none" stroke="#00aeef" opacity=".35"/>',
        '    <text x="600" y="114" text-anchor="middle" fill="#5b718e" font-family="Arial,Helvetica,sans-serif" font-size="11" font-weight="800" letter-spacing="5">RUN TERMINATED // SELF COLLISION</text>',
        '    <text x="600" y="168" text-anchor="middle" fill="#effcff" font-family="Arial,Helvetica,sans-serif" font-size="48" font-weight="900" letter-spacing="10" filter="url(#glow)">GAME OVER</text>',
        '    <line x1="356" y1="190" x2="844" y2="190" stroke="#173253"/>',
        '    <g font-family="Arial,Helvetica,sans-serif" text-anchor="middle">',
        f'      <text x="390" y="218" fill="#4d6481" font-size="10" font-weight="700" letter-spacing="2">SCORE</text><text x="390" y="244" fill="#7debff" font-size="22" font-weight="900" letter-spacing="3">{len(foods) * POINTS_PER_FOOD:06d}</text>',
        f'      <text x="530" y="218" fill="#4d6481" font-size="10" font-weight="700" letter-spacing="2">FOOD</text><text x="530" y="244" fill="#eafcff" font-size="22" font-weight="900">{len(foods)}</text>',
        f'      <text x="670" y="218" fill="#4d6481" font-size="10" font-weight="700" letter-spacing="2">LENGTH</text><text x="670" y="244" fill="#eafcff" font-size="22" font-weight="900">{max_length}</text>',
        f'      <text x="810" y="218" fill="#4d6481" font-size="10" font-weight="700" letter-spacing="2">TIME</text><text x="810" y="244" fill="#eafcff" font-size="22" font-weight="900">00:{collision_time:04.1f}</text>',
        '    </g>',
        '    <text x="600" y="271" text-anchor="middle" fill="#155eef" font-family="Arial,Helvetica,sans-serif" font-size="10" font-weight="800" letter-spacing="4">REBOOTING MATCH...</text>',
        f'    <animate attributeName="opacity" values="0;0;1;1;0" keyTimes="{game_times}" dur="{TOTAL_SECONDS}s" repeatCount="indefinite"/>',
        '  </g>',
        '</svg>',
    ])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "assets" / "contribution-game.svg"
    output.write_text(build_svg(), encoding="utf-8")
    print(f"wrote {output}")
