/** 桌码：MILKTEA:<门店id>:<桌号> */
import { request } from './request'

export async function resolveTable(scene) {
	const data = await request({
		url: '/tables/resolve',
		method: 'POST',
		data: { scene },
		auth: false
	})
	return {
		storeId: data.store_id,
		storeName: data.store_name,
		tableNo: data.table_no
	}
}
