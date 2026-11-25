// Carousel brand kit: one call per 1080x1350pt slide. The pipeline copies this file next to
// each slide, so markup starts with `#import "brand.typ": *` (the slide prefix does it).
#let night = rgb("#0E1A2B")
#let gold = rgb("#F2B84B")
#let snow = rgb("#FFFFFF")
#let levels = (low: rgb("#3BB273"), medium: gold, high: rgb("#F08C3A"), peak: rgb("#E5484D"))
#let display = "Lilita One"

#let slide(handle: "", n: none, of: none, bg: none, body) = {
  set page(width: 1080pt, height: 1350pt, margin: 0pt, fill: night)
  set text(font: "Inter", size: 40pt, fill: snow)
  if bg != none {
    place(image(bg, width: 100%, height: 100%, fit: "cover"))
    // Clear at the top where the photo speaks, dark at the bottom where the text sits.
    place(rect(width: 100%, height: 100%, fill: gradient.linear(
      (night.transparentize(100%), 0%), (night.transparentize(100%), 30%),
      (night.transparentize(15%), 70%), (night.transparentize(5%), 100%), angle: 90deg)))
  }
  if n != none and of != none {
    place(top + right, dx: -56pt, dy: 56pt, box(fill: night.transparentize(35%), radius: 40pt,
      inset: (x: 22pt, y: 12pt), text(size: 28pt, weight: "semibold")[#n/#of]))
  }
  if handle != "" {
    place(bottom + left, dx: 72pt, dy: -56pt,
      text(size: 28pt, weight: "semibold", fill: snow.transparentize(15%))[#handle])
  }
  place(bottom + left, dx: 72pt, dy: -130pt, block(width: 936pt, body))
}

#let headline(size, content, leading: 0.65em) = {
  set par(leading: leading)
  text(font: display, size: size, content)
}

#let kicker(content) = box(fill: gold, radius: 8pt, inset: (x: 18pt, y: 10pt),
  text(size: 28pt, weight: "bold", fill: night, upper(content)))

// Bodies are stacks: their gaps are explicit, whatever the paragraph spacing.
#let cover(handle: "", of: none, bg: none, kick: "", title: "", sub: "") = slide(
  handle: handle, n: 1, of: of, bg: bg, stack(dir: ttb,
    ..if kick != "" { (kicker(kick), 48pt) },
    headline(124pt, title, leading: 0.25em),
    ..if sub != "" { (80pt, text(size: 44pt, weight: "medium")[#sub]) },
    72pt,
    box(fill: gold, radius: 40pt, inset: (x: 26pt, y: 14pt),
      text(size: 30pt, weight: "bold", fill: night)[Swipe →]),
  ))

#let point(handle: "", n: none, of: none, bg: none, num: "", title: "", body: "") = slide(
  handle: handle, n: n, of: of, bg: bg, stack(dir: ttb,
    ..if num != "" { (text(font: display, size: 96pt, fill: gold)[#num], 32pt) },
    headline(84pt, title, leading: 0.3em),
    ..if body != "" { (64pt, { set par(leading: 0.55em); text(size: 40pt)[#body] }) },
  ))

// rows: ((label, level, note), ...) with level one of low, medium, high, peak.
#let data(handle: "", n: none, of: none, bg: none, title: "", rows: ()) = slide(
  handle: handle, n: n, of: of, bg: bg, stack(dir: ttb, spacing: 14pt,
    headline(76pt, title),
    40pt,
    ..rows.map(((label, level, note)) => box(width: 100%, fill: night.transparentize(25%),
      radius: 16pt, inset: 22pt, grid(
        columns: (1fr, auto), align: (left + horizon, right + horizon),
        text(size: 38pt, weight: "semibold")[#label],
        box(fill: levels.at(level), radius: 30pt, inset: (x: 20pt, y: 8pt),
          text(size: 28pt, weight: "bold", fill: night)[#note])))),
  ))

#let cta(handle: "", n: none, of: none, bg: none, title: "", ask: "") = slide(
  n: n, of: of, bg: bg, stack(dir: ttb,
    headline(96pt, title, leading: 0.25em),
    72pt,
    { set par(leading: 0.5em); text(size: 44pt, weight: "medium")[#ask] },
    88pt,
    text(size: 52pt, weight: "bold", fill: gold)[#handle],
  ))
