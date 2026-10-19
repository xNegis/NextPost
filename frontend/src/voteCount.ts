export function voteCountLabel(count: number): string {
  return count === 1 ? "1 vote" : `${count} votes`;
}
