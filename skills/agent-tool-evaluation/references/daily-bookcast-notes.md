# daily-bookcast — Session Notes

**Date**: 2026-08-01
**Source**: https://github.com/GODGOD126/daily-bookcast

## What It Is

A skill for generating Chinese audiobook-style scripts from book names. Converts books into 6,900-10,600 character scripts suitable for TTS or direct listening.

## Key Limitation

**Does NOT accept e-book files** (`.epub`, `.mobi`, etc.). The user provides a book NAME, and the skill searches public sources (Wikipedia, book reviews, summaries) to verify facts and generate the script.

## Use Case

- User says: "请把《万历十五年》写成一篇适合直接收听的中文听书稿"
- Skill searches public web sources for information about the book
- Generates a script in natural, conversational Chinese
- Output is ready for TTS or direct listening

## Limitations

- Requires the book to have sufficient public information available
- Cannot use paid/pirated content
- 8-minute hard timeout per generation
- Only uses legally accessible sources for fact-checking

## Installation

```powershell
npx skills add GODGOD126/daily-bookcast@daily-bookcast -g -y
```

## Usage

```
$daily-bookcast 《思考，快与慢》
```

Or natural language:
```
请把《万历十五年》写成一篇适合直接收听的中文听书稿。
```