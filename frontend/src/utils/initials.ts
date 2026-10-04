export function getInitials(name: string): string {
  const parts = name.trim().split(/[\s._-]+/).filter(Boolean);
  if (parts.length === 0) return '?';

  const letters =
    parts.length === 1
      ? Array.from(parts[0]).slice(0, 2).join('')
      : Array.from(parts[0])[0] + Array.from(parts[1])[0];

  return letters.toUpperCase();
}