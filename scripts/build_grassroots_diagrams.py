"""Generate the setup diagrams for the U8 grassroots coaching reference.

One SVG per activity, written to assets/images/grassroots/<id>.svg and shown on
the drill cards at /soccer/project-2030/grassroots-coaching/. The ids here must
match the activity ids in _data/grassroots_u8.yml.

These are our own drawings. The diagrams inside the source session PDFs carry a
third-party copyright notice and are deliberately not reproduced.

Run:  python scripts/build_grassroots_diagrams.py
"""

import math
import os

W, H = 440, 300
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "assets", "images", "grassroots")

TURF = "#3f7d55"
TURF_ALT = "#438457"
LINE = "rgba(255,255,255,.62)"
INK = "#0d2440"
CONE = "#f0932b"
COACH = "#ef233c"
ZONE = "rgba(255,255,255,.16)"

FONT = ("font-family=\"'Oswald','Arial Narrow',Arial,sans-serif\" "
        "font-weight=\"600\"")


class Canvas(object):
    def __init__(self):
        self.parts = []

    def add(self, markup):
        self.parts.append(markup)

    def render(self, title):
        defs = (
            '<defs>'
            '<marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" '
            'markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">'
            '<path d="M0,1 L9,5 L0,9 z" fill="#fff"/></marker>'
            '<marker id="ahp" viewBox="0 0 10 10" refX="8.5" refY="5" '
            'markerWidth="5.5" markerHeight="5.5" orient="auto-start-reverse">'
            '<path d="M0,1 L9,5 L0,9 z" fill="rgba(255,255,255,.72)"/></marker>'
            '</defs>'
        )
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'role="img" aria-label="%s">%s%s</svg>\n'
            % (W, H, esc(title), defs, "".join(self.parts))
        )


def esc(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


# --- pieces ----------------------------------------------------------------

def pitch(c, x, y, w, h, stripes=4):
    c.add('<rect x="%g" y="%g" width="%g" height="%g" rx="4" fill="%s"/>'
          % (x, y, w, h, TURF))
    if stripes:
        band = h / float(stripes)
        for i in range(stripes):
            if i % 2:
                c.add('<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>'
                      % (x, y + i * band, w, band, TURF_ALT))
    c.add('<rect x="%g" y="%g" width="%g" height="%g" rx="4" fill="none" '
          'stroke="%s" stroke-width="2"/>' % (x, y, w, h, LINE))


def line(c, x1, y1, x2, y2, dash="5 5"):
    c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="2" '
          'stroke-dasharray="%s"/>' % (x1, y1, x2, y2, LINE, dash))


def zone(c, x, y, w, h):
    c.add('<rect x="%g" y="%g" width="%g" height="%g" fill="%s"/>'
          % (x, y, w, h, ZONE))
    c.add('<rect x="%g" y="%g" width="%g" height="%g" fill="none" stroke="%s" '
          'stroke-width="2" stroke-dasharray="5 5"/>' % (x, y, w, h, LINE))


def goal(c, cx, cy, side, span=44):
    """A goal sitting on the boundary, drawn inside the field so it stays
    legible - a white outline on the pale card background would vanish."""
    d = 11
    if side == "n":
        x, y, w, h = cx - span / 2.0, cy, span, d
    elif side == "s":
        x, y, w, h = cx - span / 2.0, cy - d, span, d
    elif side == "w":
        x, y, w, h = cx, cy - span / 2.0, d, span
    else:
        x, y, w, h = cx - d, cy - span / 2.0, d, span
    c.add('<rect x="%g" y="%g" width="%g" height="%g" fill="rgba(13,36,64,.45)" '
          'stroke="#fff" stroke-width="2.8" stroke-linejoin="round"/>'
          % (x, y, w, h))


def cone(c, x, y, size=6):
    c.add('<path d="M%g,%g L%g,%g L%g,%g z" fill="%s"/>'
          % (x, y - size, x - size * 0.72, y + size * 0.6,
             x + size * 0.72, y + size * 0.6, CONE))


def gate(c, x1, y1, x2, y2):
    cone(c, x1, y1)
    cone(c, x2, y2)
    c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="1.6" '
          'stroke-dasharray="4 4"/>' % (x1, y1, x2, y2, "rgba(255,255,255,.55)"))


def triangle_goal(c, cx, cy, r=15):
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
           for a in (-90, 30, 150)]
    c.add('<path d="M%g,%g L%g,%g L%g,%g z" fill="rgba(255,255,255,.14)" '
          'stroke="rgba(255,255,255,.6)" stroke-width="1.6" '
          'stroke-dasharray="4 4"/>'
          % (pts[0][0], pts[0][1], pts[1][0], pts[1][1], pts[2][0], pts[2][1]))
    for px, py in pts:
        cone(c, px, py, 5)


def attacker(c, x, y, label=None):
    c.add('<circle cx="%g" cy="%g" r="9.5" fill="#fff" stroke="%s" '
          'stroke-width="2"/>' % (x, y, INK))
    if label:
        c.add('<text x="%g" y="%g" text-anchor="middle" fill="%s" '
              'font-size="10" %s>%s</text>' % (x, y + 3.5, INK, FONT, esc(label)))


def defender(c, x, y, label=None):
    c.add('<rect x="%g" y="%g" width="15" height="15" rx="2" fill="%s" '
          'stroke="#fff" stroke-width="2" transform="rotate(45 %g %g)"/>'
          % (x - 7.5, y - 7.5, INK, x, y))
    if label:
        c.add('<text x="%g" y="%g" text-anchor="middle" fill="#fff" '
              'font-size="9" %s>%s</text>' % (x, y + 3.2, FONT, esc(label)))


def coach(c, x, y):
    c.add('<rect x="%g" y="%g" width="20" height="20" rx="4" fill="%s" '
          'stroke="#fff" stroke-width="2"/>' % (x - 10, y - 10, COACH))
    c.add('<text x="%g" y="%g" text-anchor="middle" fill="#fff" font-size="11" '
          '%s>C</text>' % (x, y + 4, FONT))


def ball(c, x, y):
    c.add('<circle cx="%g" cy="%g" r="4.4" fill="#fff" stroke="%s" '
          'stroke-width="1.6"/>' % (x, y, INK))
    c.add('<circle cx="%g" cy="%g" r="1.5" fill="%s"/>' % (x, y, INK))


def pass_arrow(c, x1, y1, x2, y2):
    c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#fff" stroke-width="2.4" '
          'marker-end="url(#ah)"/>' % (x1, y1, x2, y2))


def run_arrow(c, x1, y1, x2, y2):
    c.add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="rgba(255,255,255,.72)" '
          'stroke-width="2.2" stroke-dasharray="6 5" marker-end="url(#ahp)"/>'
          % (x1, y1, x2, y2))


def dribble(c, x1, y1, x2, y2, amp=5.5):
    """A wavy line, the way a ball travels at someone's feet."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    if length < 1:
        return
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    waves = max(2, int(length / 22))
    steps = waves * 8
    pts = []
    for i in range(steps + 1):
        t = i / float(steps)
        off = math.sin(t * waves * 2 * math.pi) * amp * (1 - t * 0.25)
        pts.append((x1 + ux * length * t + px * off,
                    y1 + uy * length * t + py * off))
    d = "M%g,%g " % pts[0] + " ".join("L%g,%g" % p for p in pts[1:])
    c.add('<path d="%s" fill="none" stroke="#fff" stroke-width="2.4" '
          'stroke-linecap="round" marker-end="url(#ah)"/>' % d)


def caption(c, x, y, text, anchor="middle", fill="rgba(255,255,255,.9)"):
    c.add('<text x="%g" y="%g" text-anchor="%s" fill="%s" font-size="11.5" '
          'letter-spacing="0.6" %s>%s</text>'
          % (x, y, anchor, fill, FONT, esc(text.upper())))


def outside_label(c, x, y, text, anchor="middle"):
    c.add('<text x="%g" y="%g" text-anchor="%s" fill="#7a8594" font-size="11.5" '
          'letter-spacing="0.6" %s>%s</text>'
          % (x, y, anchor, FONT, esc(text.upper())))


def queue(c, x, y, n=3, dx=0, dy=18, kind="a"):
    for i in range(n):
        if kind == "a":
            attacker(c, x + dx * i, y + dy * i)
        else:
            defender(c, x + dx * i, y + dy * i)


# --- diagrams ---------------------------------------------------------------

def d_arrival_game(c):
    for i, x in enumerate((22, 236)):
        pitch(c, x, 40, 182, 236, stripes=4)
        goal(c, x + 91, 40, "n")
        goal(c, x + 91, 276, "s")
    attacker(c, 90, 210); ball(c, 101, 218)
    dribble(c, 104, 200, 113, 92)
    defender(c, 128, 150)
    attacker(c, 290, 214); ball(c, 301, 222)
    attacker(c, 350, 170)
    pass_arrow(c, 308, 206, 342, 182)
    defender(c, 300, 132); defender(c, 358, 226)
    outside_label(c, 22, 26, "Start here", "start")
    outside_label(c, 418, 26, "Then start a second game", "end")
    outside_label(c, 220, 296, "Add each kid as they turn up")


def d_the_game(c):
    pitch(c, 20, 30, 400, 240, stripes=4)
    goal(c, 20, 150, "w", 60)
    goal(c, 420, 150, "e", 60)
    for x, y in ((110, 90), (150, 190), (230, 60), (250, 150)):
        attacker(c, x, y)
    for x, y in ((190, 120), (300, 96), (318, 202), (356, 106)):
        defender(c, x, y)
    ball(c, 262, 158)
    pass_arrow(c, 160, 182, 224, 72)
    dribble(c, 272, 154, 388, 150)


def d_partner_bandits(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    gate(c, 160, 34, 280, 34)
    gate(c, 160, 266, 280, 266)
    outside_label(c, 220, 24, "Goal")
    outside_label(c, 220, 290, "Goal")
    attacker(c, 100, 200); ball(c, 111, 208)
    attacker(c, 148, 150)
    pass_arrow(c, 118, 192, 140, 164)
    dribble(c, 156, 138, 200, 54)
    attacker(c, 330, 210); ball(c, 341, 218)
    attacker(c, 372, 158)
    defender(c, 230, 150, "B")
    defender(c, 290, 108, "B")
    run_arrow(c, 244, 158, 316, 200)


def d_four_corner_goals(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    for x in (95, 345):
        goal(c, x, 34, "n", 60)
        goal(c, x, 266, "s", 60)
    attacker(c, 170, 200); ball(c, 181, 208)
    attacker(c, 260, 190)
    defender(c, 180, 130); defender(c, 268, 118)
    pass_arrow(c, 190, 198, 250, 192)
    dribble(c, 272, 180, 336, 62)


def d_boston_bulldogs(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    zone(c, 20, 122, 400, 56)
    caption(c, 220, 156, "The pound")
    goal(c, 220, 34, "n", 66)
    goal(c, 220, 266, "s", 66)
    defender(c, 140, 150); defender(c, 300, 150)
    coach(c, 220, 96)
    attacker(c, 100, 236); ball(c, 111, 244)
    attacker(c, 176, 232)
    dribble(c, 112, 226, 130, 76)
    attacker(c, 330, 238); ball(c, 341, 246)
    attacker(c, 384, 214)
    pass_arrow(c, 348, 232, 378, 194)


def d_end_zones_1v1(c):
    for x in (22, 236):
        pitch(c, x, 34, 182, 232, stripes=4)
        zone(c, x, 34, 182, 40)
        zone(c, x, 226, 182, 40)
    caption(c, 113, 58, "Zone"); caption(c, 327, 58, "Zone")
    attacker(c, 74, 208); ball(c, 85, 216)
    dribble(c, 88, 200, 104, 88)
    defender(c, 140, 152)
    run_arrow(c, 134, 142, 116, 106)
    attacker(c, 300, 214); ball(c, 311, 222)
    attacker(c, 356, 200)
    defender(c, 306, 140); defender(c, 358, 148)
    pass_arrow(c, 318, 208, 346, 202)


def d_guard_the_goals(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    spots = ((110, 96), (250, 78), (350, 150), (150, 216), (300, 226))
    for sx, sy in spots:
        triangle_goal(c, sx, sy)
    defender(c, 178, 110); defender(c, 288, 128); defender(c, 336, 194)
    attacker(c, 62, 168); ball(c, 73, 176)
    attacker(c, 108, 168)
    dribble(c, 78, 166, 232, 92)
    attacker(c, 214, 246); ball(c, 225, 254)
    attacker(c, 262, 262)
    pass_arrow(c, 232, 244, 288, 236)


def d_four_corner_shoot_defend(c):
    pitch(c, 96, 34, 264, 232, stripes=4)
    goal(c, 228, 34, "n", 62)
    goal(c, 228, 266, "s", 62)
    coach(c, 46, 150)
    ball(c, 46, 176); ball(c, 34, 190); ball(c, 58, 190)
    outside_label(c, 46, 214, "Balls")
    queue(c, 116, 16, 2, dx=26, dy=0, kind="a")
    queue(c, 314, 16, 2, dx=26, dy=0, kind="a")
    queue(c, 116, 288, 2, dx=26, dy=0, kind="d")
    queue(c, 314, 288, 2, dx=26, dy=0, kind="d")
    attacker(c, 190, 122); ball(c, 201, 130)
    attacker(c, 264, 106)
    defender(c, 200, 190); defender(c, 272, 176)
    run_arrow(c, 70, 150, 150, 150)
    dribble(c, 204, 116, 224, 60)


def d_defend_3_goals_counter(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    for x in (100, 220, 340):
        goal(c, x, 34, "n", 52)
    outside_label(c, 220, 24, "Three goals to attack")
    goal(c, 220, 266, "s", 52)
    outside_label(c, 220, 290, "One goal to counter into")
    attacker(c, 178, 196); ball(c, 189, 204)
    attacker(c, 262, 186)
    defender(c, 168, 124); defender(c, 258, 112)
    pass_arrow(c, 196, 192, 250, 188)
    dribble(c, 272, 176, 330, 62)


def d_defend_your_goal(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    zone(c, 20, 34, 400, 44)
    caption(c, 220, 60, "Scoring zone")
    goal(c, 220, 266, "s", 62)
    defender(c, 162, 190); defender(c, 206, 216); defender(c, 300, 188)
    attacker(c, 150, 116); ball(c, 161, 124)
    attacker(c, 244, 104); attacker(c, 340, 128)
    pass_arrow(c, 166, 124, 232, 110)
    dribble(c, 250, 118, 232, 246)
    run_arrow(c, 312, 176, 352, 94)
    outside_label(c, 220, 290, "Defenders break out to the zone")


def d_groups_of_2_vs_defenders(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    for x in (100, 220, 340):
        goal(c, x, 34, "n", 50)
        goal(c, x, 266, "s", 50)
    defender(c, 160, 150); defender(c, 286, 150)
    attacker(c, 96, 214); ball(c, 107, 222)
    attacker(c, 210, 226)
    pass_arrow(c, 114, 212, 194, 224)
    dribble(c, 218, 214, 226, 64)
    attacker(c, 330, 214); ball(c, 341, 222)
    attacker(c, 382, 190)


def d_defend_each_zone(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    line(c, 20, 111, 420, 111)
    line(c, 20, 189, 420, 189)
    goal(c, 220, 34, "n", 62)
    goal(c, 220, 266, "s", 62)
    defender(c, 300, 228); defender(c, 148, 150); defender(c, 296, 72)
    attacker(c, 110, 240); ball(c, 121, 248)
    attacker(c, 190, 232)
    pass_arrow(c, 128, 238, 174, 234)
    dribble(c, 198, 220, 214, 62)
    outside_label(c, 430, 232, "1", "end")
    outside_label(c, 430, 156, "2", "end")
    outside_label(c, 430, 78, "3", "end")


def d_side_goals_2v1(c):
    pitch(c, 92, 34, 268, 232, stripes=4)
    goal(c, 140, 34, "n", 52)
    goal(c, 312, 266, "s", 52)
    coach(c, 46, 150)
    ball(c, 46, 176); ball(c, 34, 190); ball(c, 58, 190)
    outside_label(c, 46, 214, "Balls")
    queue(c, 404, 96, 3, dx=0, dy=26, kind="a")
    outside_label(c, 404, 78, "Two go on", "end")
    queue(c, 46, 96, 1, kind="d")
    outside_label(c, 46, 78, "One goes on", "start")
    attacker(c, 200, 194); ball(c, 211, 202)
    attacker(c, 268, 168)
    defender(c, 244, 116)
    pass_arrow(c, 218, 190, 254, 176)
    dribble(c, 200, 182, 150, 70)
    run_arrow(c, 388, 174, 366, 174)


def d_festival(c):
    for x in (22, 236):
        pitch(c, x, 44, 182, 212, stripes=4)
        goal(c, x + 91, 44, "n", 52)
        goal(c, x + 91, 256, "s", 52)
    for x, y in ((70, 200), (132, 176), (100, 226)):
        attacker(c, x, y)
    for x, y in ((78, 108), (140, 96), (108, 140)):
        defender(c, x, y)
    for x, y in ((286, 196), (346, 178), (316, 230)):
        attacker(c, x, y)
    for x, y in ((292, 106), (352, 96), (322, 140)):
        defender(c, x, y)
    ball(c, 112, 168); ball(c, 328, 164)
    outside_label(c, 22, 30, "Field 1", "start")
    outside_label(c, 236, 30, "Field 2", "start")
    outside_label(c, 418, 288, "Swap teams each round", "end")


def d_freeze_tag_layered(c):
    pitch(c, 60, 30, 320, 240, stripes=4)
    spots = ((120, 90), (210, 70), (300, 106), (140, 190), (250, 176), (320, 216))
    for sx, sy in spots:
        attacker(c, sx, sy)
        ball(c, sx + 12, sy + 9)
    dribble(c, 132, 100, 196, 156)
    defender(c, 214, 122, "F")
    run_arrow(c, 226, 130, 288, 166)
    attacker(c, 190, 228)
    ball(c, 190, 208)
    outside_label(c, 190, 290, "Frozen - ball above your head")


def d_1v1_two_goals(c):
    pitch(c, 84, 34, 272, 232, stripes=4)
    goal(c, 140, 34, "n", 52)
    goal(c, 302, 34, "n", 52)
    attacker(c, 220, 214); ball(c, 231, 222)
    defender(c, 214, 140)
    dribble(c, 226, 204, 150, 64)
    run_arrow(c, 240, 208, 300, 82)


def d_2v2_to_cones(c):
    pitch(c, 20, 66, 400, 168, stripes=3)
    for y in (100, 150, 200):
        cone(c, 26, y)
        cone(c, 414, y)
    outside_label(c, 26, 50, "Targets", "start")
    outside_label(c, 414, 50, "Targets", "end")
    attacker(c, 152, 126); ball(c, 163, 134)
    attacker(c, 196, 194)
    defender(c, 248, 118); defender(c, 286, 206)
    pass_arrow(c, 166, 138, 186, 180)
    dribble(c, 208, 186, 400, 152)


def d_four_goal_game(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    for x in (128, 312):
        goal(c, x, 34, "n", 56)
        goal(c, x, 266, "s", 56)
    attacker(c, 172, 196); ball(c, 183, 204)
    attacker(c, 268, 214)
    defender(c, 210, 134); defender(c, 262, 176)
    dribble(c, 186, 190, 130, 62)
    run_arrow(c, 280, 206, 312, 246)


def d_get_outta_there(c):
    pitch(c, 118, 34, 244, 232, stripes=4)
    goal(c, 240, 34, "n", 58)
    goal(c, 240, 266, "s", 58)
    coach(c, 60, 150)
    ball(c, 60, 176); ball(c, 48, 190); ball(c, 72, 190)
    queue(c, 34, 74, 3, dx=0, dy=24, kind="a")
    queue(c, 88, 74, 3, dx=0, dy=24, kind="d")
    run_arrow(c, 84, 150, 132, 150)
    attacker(c, 196, 178); ball(c, 207, 186)
    attacker(c, 268, 200)
    defender(c, 204, 110); defender(c, 282, 126)
    dribble(c, 210, 170, 236, 62)
    outside_label(c, 60, 224, "Next two on")


def d_dribble_gates(c):
    pitch(c, 30, 30, 380, 240, stripes=4)
    gates = (((92, 74), (128, 62)), ((214, 60), (250, 76)),
             ((330, 96), (352, 126)), ((88, 176), (110, 206)),
             ((208, 208), (244, 216)), ((316, 196), (344, 218)))
    for (x1, y1), (x2, y2) in gates:
        gate(c, x1, y1, x2, y2)
    for sx, sy in ((70, 128), (170, 150), (272, 128), (150, 250), (300, 258)):
        attacker(c, sx, sy)
        ball(c, sx + 12, sy + 9)
    dribble(c, 82, 120, 108, 78)
    dribble(c, 182, 142, 228, 74)
    dribble(c, 284, 134, 336, 118)


def d_sharks_and_minnows(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    zone(c, 20, 118, 400, 64)
    caption(c, 220, 156, "Sharks")
    defender(c, 128, 150); defender(c, 332, 150)
    for i, sx in enumerate((80, 150, 220, 290, 360)):
        attacker(c, sx, 244)
        ball(c, sx + 12, 252)
    dribble(c, 92, 236, 108, 62)
    dribble(c, 302, 236, 286, 62)
    outside_label(c, 220, 290, "Start here")
    outside_label(c, 220, 24, "Get to this side")


def d_end_zone_soccer(c):
    pitch(c, 20, 34, 400, 232, stripes=4)
    zone(c, 20, 34, 400, 42)
    zone(c, 20, 224, 400, 42)
    caption(c, 220, 60, "Zone"); caption(c, 220, 250, "Zone")
    attacker(c, 150, 186); ball(c, 161, 194)
    attacker(c, 246, 200)
    defender(c, 158, 122); defender(c, 258, 132)
    pass_arrow(c, 166, 192, 230, 200)
    dribble(c, 254, 188, 268, 88)


def d_numbers_game(c):
    pitch(c, 96, 34, 264, 232, stripes=4)
    goal(c, 228, 34, "n", 60)
    goal(c, 228, 266, "s", 60)
    queue(c, 60, 88, 4, dx=0, dy=26, kind="a")
    queue(c, 396, 88, 4, dx=0, dy=26, kind="d")
    coach(c, 228, 288)
    outside_label(c, 60, 68, "Team A")
    outside_label(c, 396, 68, "Team B")
    run_arrow(c, 78, 130, 128, 142)
    run_arrow(c, 378, 130, 328, 142)
    attacker(c, 168, 168); ball(c, 179, 176)
    attacker(c, 236, 196)
    defender(c, 190, 108); defender(c, 288, 150)
    dribble(c, 182, 160, 218, 62)


DIAGRAMS = {
    "arrival-game": d_arrival_game,
    "the-game": d_the_game,
    "partner-bandits": d_partner_bandits,
    "four-corner-goals": d_four_corner_goals,
    "boston-bulldogs": d_boston_bulldogs,
    "end-zones-1v1": d_end_zones_1v1,
    "guard-the-goals": d_guard_the_goals,
    "four-corner-shoot-defend": d_four_corner_shoot_defend,
    "defend-3-goals-counter": d_defend_3_goals_counter,
    "defend-your-goal": d_defend_your_goal,
    "groups-of-2-vs-defenders": d_groups_of_2_vs_defenders,
    "defend-each-zone": d_defend_each_zone,
    "side-goals-2v1": d_side_goals_2v1,
    "festival": d_festival,
    "freeze-tag-layered": d_freeze_tag_layered,
    "1v1-two-goals": d_1v1_two_goals,
    "2v2-to-cones": d_2v2_to_cones,
    "four-goal-game": d_four_goal_game,
    "get-outta-there": d_get_outta_there,
    "dribble-gates": d_dribble_gates,
    "sharks-and-minnows": d_sharks_and_minnows,
    "end-zone-soccer": d_end_zone_soccer,
    "numbers-game": d_numbers_game,
}


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for name, draw in sorted(DIAGRAMS.items()):
        c = Canvas()
        draw(c)
        path = os.path.join(OUT, name + ".svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(c.render("Setup diagram"))
        print("wrote", os.path.relpath(path))
    print("%d diagrams" % len(DIAGRAMS))


if __name__ == "__main__":
    main()
