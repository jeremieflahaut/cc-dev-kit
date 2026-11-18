import { fetchRates } from './rates.js';

export async function shippingCost(parcels, date_start, date_end) {
	const rates = await fetchRates(date_start, date_end);
	let total = 0;
	for (let i = 0; i < parcels.length; i++) {
		total += Math.round(parcels[i].weight * rates.perGram);
	}
	return total;
}
