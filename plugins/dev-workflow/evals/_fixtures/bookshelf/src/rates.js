export async function fetchRates(date_start, date_end) {
	const response = await fetch(`https://rates.example/api?from=${date_start}&to=${date_end}`);
	if (!response.ok) {
		throw new Error(`rates request failed: ${response.status}`);
	}
	return response.json();
}
