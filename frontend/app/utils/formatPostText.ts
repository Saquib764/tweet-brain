export type PostTextPart =
  | { type: 'text', text: string }
  | { type: 'mention', handle: string, href: string }

const MENTION_REGEX = /(?<![A-Za-z0-9.])@([A-Za-z0-9_]{1,15})\b/g

function mentionHref(handle: string) {
  return `https://x.com/${handle}`
}

export function formatPostText(text: string): PostTextPart[] {
  const parts: PostTextPart[] = []
  let lastIndex = 0

  for (const match of text.matchAll(MENTION_REGEX)) {
    const index = match.index ?? 0
    if (index > lastIndex) {
      parts.push({ type: 'text', text: text.slice(lastIndex, index) })
    }

    const handle = match[1]!
    parts.push({
      type: 'mention',
      handle,
      href: mentionHref(handle),
    })
    lastIndex = index + match[0].length
  }

  if (lastIndex < text.length) {
    parts.push({ type: 'text', text: text.slice(lastIndex) })
  }

  return parts.length > 0 ? parts : [{ type: 'text', text }]
}
