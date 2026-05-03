---
title: "LinkBridge"
date: 2026-02-08
summary: "macOS menu bar app — bridges Ableton Link to a MIDI clock output to sync hardware sequencers (Novation Circuit Tracks et al.) to djay Pro / Mixxx / Ableton Live."
tags: ["python", "macos", "audio", "midi", "ableton-link"]
weight: 3
cover:
  image: "/images/linkbridge/cover.jpg"
  alt: "LinkBridge architecture diagram"
  caption: ""
ShowReadingTime: false
ShowToc: false
---

**GitHub:** [github.com/AnyByte/LinkBridge](https://github.com/AnyByte/LinkBridge)

**Stack:** Python · rumps · mido · Ableton Link Python bindings · py2app

## The itch

I DJ at home with djay Pro, Mixxx, and Ableton Live, and my hardware sampler — a Novation Circuit Tracks — needs to play in tempo with whatever's running on the laptop. The Circuit understands MIDI clock; the laptop apps speak Ableton Link. The two don't talk natively, so without something in between you're back to manual tap-tempo every time you start a set.

## The solution

LinkBridge is a tiny menu-bar app that joins the Ableton Link session, listens for tempo changes, and broadcasts MIDI clock messages at 24 PPQ to a virtual MIDI port — which the Circuit (and any other clock-following hardware) picks up. The whole thing is a few hundred lines of Python: `mido` for MIDI out, the Link Python bindings for tempo sync, `rumps` for the menu-bar UI, `py2app` for packaging, and `create-dmg` for one-click install.

## Status

Done what I needed it to do, runs in my home studio every week. Code is on GitHub if anyone wants the same trick for their own setup.
