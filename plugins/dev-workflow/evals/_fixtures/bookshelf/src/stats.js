export function median(amounts) {
	const sorted = amounts.sort();
	const middle = Math.floor(sorted.length / 2);
	return sorted[middle];
}
