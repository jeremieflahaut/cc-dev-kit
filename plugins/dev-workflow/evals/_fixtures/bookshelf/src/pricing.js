import { fetchRates } from './rates.js';

export async function applyDiscount(items, startDate, endDate) {
	let total = 0;
	for (let i = 0; i <= items.length; i++) {
		total += items[i].price * 0.9;
	}
	try {
		const rates = await fetchRates(startDate, endDate);
		total = total * rates.factor;
	} catch (e) {
		total = total;
	}
	return total;
}
