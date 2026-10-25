<template>
	<view class="page">
		<!-- ① 顶栏：自取 | 外送 + 搜索（右侧留给微信胶囊） -->
		<view class="topbar" :style="{ paddingTop: safeTop, paddingRight: capPad + 'px' }">
			<view class="mode">
				<text class="mode-t" :class="{ on: mode === '自取' }" @tap="setMode('自取')">自取</text>
				<view class="mode-div"></view>
				<text class="mode-t" :class="{ on: mode === '外送' }" @tap="setMode('外送')">外送</text>
			</view>
			<view class="tb-actions">
				<view class="tb-scan" hover-class="hv" @tap="scanTable">
					<text class="tb-scan-t">扫码</text>
				</view>
				<view class="tb-search" hover-class="hv" @tap="onSearch">
					<uni-icons type="search" size="20" color="#3d3229"></uni-icons>
				</view>
			</view>
		</view>

		<!-- ② 门店行（点击 → 地图选店弹层） -->
		<view class="store-row" hover-class="hv" @tap="storePick = true">
			<view class="st-left">
				<view class="st-name">
					<uni-icons type="star-filled" size="17" color="#E8833A"></uni-icons>
					<text class="st-title">{{ selStore.name }}</text>
					<text class="st-arrow">›</text>
				</view>
				<view class="st-meta">
					<text class="st-dist-t">距您 {{ selStore.dist }}</text>
					<text class="st-dot">·</text>
					<text class="st-status">{{ selStore.statusText }}</text>
					<view class="st-live">
						<view class="st-live-dot"></view>
						<text class="st-live-t">当前 {{ selStore.makingCups }} 杯制作中</text>
					</view>
				</view>
			</view>
			<view class="st-badge">
				<text class="stb-t1">拼单</text>
				<text class="stb-t2">享优惠</text>
			</view>
		</view>

		<!-- 扫码桌号：堂食上下文 -->
		<view class="table-bar" v-if="tableCtx">
			<text class="tb-tag">堂食</text>
			<text class="tbb-name">{{ tableCtx.storeName }}</text>
			<text class="tbb-no">{{ tableCtx.tableNo }} 桌</text>
			<text class="tbb-clear" hover-class="hv" @tap="dropTable">取消</text>
		</view>

		<!-- ⑤ 页签 -->
		<view class="mtabs">
			<view
				v-for="tb in tabs"
				:key="tb.id"
				class="mt-tab"
				:class="{ on: tabId === tb.id }"
				hover-class="hv"
				@tap="pickTab(tb.id)"
			>
				<text class="mt-t">{{ tb.name }}</text>
				<view class="mt-bar"></view>
			</view>
		</view>

		<!-- ⑥ 左侧分类 + 右侧商品列表 -->
		<view class="content">
			<category-rail :items="categories" :active="sideId" @pick="pickCategory" />

			<!-- 连续分节滚动：券包置顶 + 全部分节，点左侧分类用锚点跳转（:key 仅跟随页签，切页签回顶） -->
			<scroll-view scroll-y class="plist" :key="tabId" :scroll-into-view="scrollInto" scroll-with-animation @scroll="onListScroll">
				<!-- 内层定宽：JS 按屏宽算出像素宽度写死，杜绝滚动内容层被撑宽（750rpx − 侧栏176 = 574rpx） -->
				<view class="plist-in" :style="{ width: listW + 'px' }">
					<!-- 券包特惠：新客 banner + 券包列表 -->
					<view id="sec-coupon" class="js-sec">
						<view class="promo-banner">
							<view class="pb-deco pb-d1"></view>
							<view class="pb-deco pb-d2"></view>
							<view class="pb-left">
								<text class="pb-tag">新朋友专享</text>
								<view class="pb-title"><text class="pb-big">首单立减 3 元</text></view>
								<text class="pb-sub2">第二杯半价 · 券包每周三更新</text>
								<view class="pb-btn" hover-class="hv" @tap="claimAll">一键领取</view>
							</view>
						</view>
						<view class="cp-head">
							<text class="cp-h-t">可领券包</text>
							<text class="cp-h-s">{{ unclaimedCount }} 张待领取</text>
						</view>
						<coupon-ticket
							v-for="cp in coupons"
							:key="cp.id"
							:coupon="cp"
							@claim="onClaim"
						/>
					</view>

					<!-- 商品分节（连续滚动，一直滑到底都有商品） -->
					<view class="sec js-sec" v-for="sec in sections" :key="sec.id" :id="'sec-' + sec.id">
						<view class="sec-head">
							<text class="sec-name" :style="{ color: sec.color }">{{ sec.name }}</text>
							<text class="sec-desc">{{ sec.desc }}</text>
						</view>
						<product-card
							v-for="dk in sec.drinks"
							:key="dk.id"
							:drink="dk"
							@detail="toDetail"
							@spec="openSpec"
						/>
					</view>
					<view class="no-drink" v-if="!sections.length">{{ loading ? '菜单加载中…' : '这个分区暂时没有饮品，看看别的吧' }}</view>
					<view class="list-pad" :class="{ withCart: cartCount }"></view>
				</view>
			</scroll-view>
		</view>

		<!-- ⑦ 购物车栏：点左侧展开已选明细，可逐项删除 -->
		<view class="mask cart-mask" v-if="cartOpen" @tap="cartOpen = false"></view>
		<view class="cart-wrap" v-if="cartCount">
			<view class="cart-panel" v-if="cartOpen">
				<view class="cpn-head">
					<text class="cpn-t">已选 {{ cartCount }} 件</text>
					<text class="cpn-s">可逐项删除</text>
				</view>
				<scroll-view scroll-y class="cpn-list">
					<view class="cpn-item" v-for="(it, i) in cart" :key="i">
						<image class="cpn-img" :src="it.product.img" mode="aspectFill"></image>
						<view class="cpn-mid">
							<text class="cpn-name">{{ it.product.name }}</text>
							<text class="cpn-spec">{{ itemSpec(it) }}</text>
						</view>
						<view class="cpn-right">
							<text class="cpn-price">¥{{ itemTotal(it) }}</text>
							<text class="cpn-count">×{{ it.count }}</text>
						</view>
						<view class="cpn-del" hover-class="hv" @tap.stop="removeItem(i)">删除</view>
					</view>
				</scroll-view>
			</view>
			<view class="cart-tip" v-if="cartSave">
				<text class="cart-save">已享会员折扣，共减免 ¥{{ cartSave }}</text>
			</view>
			<view class="cart-bar">
				<view class="cb-left" @tap="toggleCart">
					<view class="cb-icon">
						<uni-icons type="cart-filled" size="24" color="#fff7ec"></uni-icons>
						<view class="cb-badge">{{ cartCount }}</view>
					</view>
					<view class="cb-price">
						<text class="cb-pre">预估</text>
						<text class="cb-sym">¥</text>
						<text class="cb-num">{{ cartTotal }}</text>
						<text class="cb-orig" v-if="cartSave">¥{{ cartTotal + cartSave }}</text>
					</view>
					<view class="cb-chev" :class="{ open: cartOpen }"></view>
				</view>
				<view class="cb-go" hover-class="hv" @tap="checkout">去结算</view>
			</view>
		</view>

		<!-- ⑧ 地图选店弹层 -->
		<view class="mask" v-if="storePick" @tap="storePick = false"></view>
		<view class="store-sheet" v-if="storePick">
			<view class="ss-handle"></view>
			<text class="ss-title">选择门店</text>
			<view class="ss-map">
				<view class="ss-block ss-b1"></view>
				<view class="ss-block ss-b2"></view>
				<view class="ss-block ss-b3"></view>
				<view class="ss-road ss-r1"></view>
				<view class="ss-road ss-r2"></view>
				<view class="ss-pin">
					<view class="ss-pin-dot"></view>
					<view class="ss-bubble">距您 205m</view>
				</view>
			</view>
			<view
				class="ss-item"
				v-for="st in stores"
				:key="st.id"
				hover-class="hv"
				@tap="pickStore(st)"
			>
				<view class="ss-radio" :class="{ on: selStoreId === st.id }"></view>
				<view class="ss-mid">
					<text class="ss-name">{{ st.name }}</text>
					<text class="ss-area">{{ st.area }} · {{ st.dist }} · {{ st.statusText }}</text>
				</view>
				<text class="ss-cur" v-if="selStoreId === st.id">当前</text>
			</view>
			<view class="ss-pad"></view>
		</view>

		<!-- ⑨ 规格选择弹层 -->
		<view class="mask" v-if="specDrink" @tap="closeSpec"></view>
		<view class="spec-sheet" v-if="specDrink">
			<view class="sp-hero" :style="{ background: lineOf(specDrink.line).bg }">
				<image class="sp-img" :src="specDrink.img" mode="aspectFill"></image>
				<view class="sp-close" hover-class="hv" @tap="closeSpec">
					<uni-icons type="closeempty" size="18" color="#fff7ec"></uni-icons>
				</view>
			</view>
			<view class="sp-info">
				<view class="sp-name-row">
					<text class="sp-name">{{ specDrink.name }}</text>
					<text class="sp-ltag" :style="{ color: lineOf(specDrink.line).color, background: '#ffffff' }">{{ lineOf(specDrink.line).tag }}</text>
				</view>
				<text class="sp-desc">{{ specDrink.desc }}</text>
			</view>
			<scroll-view scroll-y class="sp-opts">
				<view :style="{ width: sys.windowWidth + 'px' }">
				<view class="sp-group">
					<text class="sp-gtitle">可选糖<text class="sp-gsub">（必选1份）</text></text>
					<view class="sp-chips">
						<view
							v-for="sg in sugarOpts"
							:key="sg"
							class="sp-chip"
							:class="{ on: spSugar === sg }"
							hover-class="hv"
							@tap="spSugar = sg"
						>{{ sg }}</view>
					</view>
				</view>
				<view class="sp-group">
					<text class="sp-gtitle">冰度<text class="sp-gsub">（必选1份）</text></text>
					<view class="sp-chips">
						<view
							v-for="ic in iceOpts"
							:key="ic"
							class="sp-chip"
							:class="{ on: spIce === ic }"
							hover-class="hv"
							@tap="spIce = ic"
						>{{ ic }}</view>
					</view>
				</view>
				<view class="sp-group">
					<text class="sp-gtitle">小料<text class="sp-gsub">（可多选）</text></text>
					<view class="sp-chips">
						<view
							v-for="tp in toppings"
							:key="tp.id"
							class="sp-chip"
							:class="{ on: hasTop(tp) }"
							hover-class="hv"
							@tap="toggleTop(tp)"
						>{{ tp.name }} +{{ tp.price }}</view>
					</view>
				</view>
				</view>
			</scroll-view>
			<view class="sp-foot">
				<view class="sp-price-row">
					<view class="p-price">
						<text class="p-sym">¥</text>
						<text class="p-num">{{ spTotal }}</text>
						<text class="p-orig" v-if="spOrigTotal">¥{{ spOrigTotal }}</text>
					</view>
					<view class="sp-count">
						<view class="sc-btn" hover-class="hv" @tap="spCount > 1 ? spCount-- : ''">－</view>
						<text class="sc-num">{{ spCount }}</text>
						<view class="sc-btn sc-add" hover-class="hv" @tap="spCount++">＋</view>
					</view>
				</view>
				<text class="sp-sum">【{{ spSpecText }}】</text>
				<view class="sp-btns">
					<view class="sp-buy" hover-class="hv" @tap="buyNow">立即购买</view>
					<view class="sp-addcart" hover-class="hv" @tap="addCart">加入购物车</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, getCurrentInstance, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import ProductCard from '@/components/menu/product-card.vue'
import CouponTicket from '@/components/menu/coupon-ticket.vue'
import CategoryRail from '@/components/menu/category-rail.vue'
import { getLines, getOptions, getProducts, getStores } from '@/common/api/catalog'
import { claimCoupon, getTemplates } from '@/common/api/coupons'
import { resolveTable } from '@/common/api/tables'
import { ensureLogin } from '@/common/api/auth'
import { showError } from '@/common/api/request'
import { toDrink } from '@/common/api/adapters'
import { getStoreId, saveStoreId } from '@/common/api/token'
import { setCheckoutDraft } from '@/common/store/session'
import { getTableContext, saveTableContext, clearTableContext } from '@/common/store/table'
import { scanCode, isScanCancel } from '@/common/utils/scan'

const lines = ref([])
const products = ref([])
const iceOpts = ref([])
const sugarOpts = ref([])
const toppings = ref([])
const coupons = ref([])
const loading = ref(false)
const unclaimedCount = computed(() => coupons.value.filter((cp) => !cp.claimed).length)

// 沉浸式顶栏
const sys = uni.getWindowInfo()
const statusBarHeight = sys.statusBarHeight
const safeTop = statusBarHeight + 4 + 'px'
// 右侧给微信原生胶囊（···|⊙）留位，避免搜索按钮被压住
let capPad = 24
try {
	const menu = uni.getMenuButtonBoundingClientRect && uni.getMenuButtonBoundingClientRect()
	if (menu && menu.width) capPad = sys.windowWidth - menu.left + 6
} catch (e) {}
// 列表定宽（px）：屏宽 × 574/750，物理防止滚动内容层溢出（750 − 侧栏176 = 574rpx）
const listW = Math.floor(sys.windowWidth * 574 / 750)

const mode = ref('自取')
const tableCtx = ref(getTableContext())
const tabId = ref('classic')
const sideId = ref('coupon')
const scrollInto = ref('')
// 双向联动：记录列表滚动位置、各分节相对内容顶部的偏移
const scrollTop = ref(0)
let secTops = []
let listViewH = 0
let linkLock = 0

const tabs = [
	{ id: 'classic', name: '经典菜单' },
	{ id: 'member', name: '会员专享价' },
	{ id: 'new', name: '新品上市' },
	{ id: 'mine', name: '我的常点' }
]

const pickTab = (id) => {
	if (tabId.value === id) return
	tabId.value = id
	sideId.value = 'all'
	scrollInto.value = ''
	loadProducts()
}

// 门店（点门店行 → 地图选店弹层切换）
const stores = ref([])
const selStoreId = ref(getStoreId())
const fallbackStore = { id: 0, name: '四猫茶学园', area: '', dist: '', statusText: '', makingCups: 0 }
const selStore = computed(() => stores.value.find(s => s.id === selStoreId.value) || stores.value[0] || fallbackStore)
const storePick = ref(false)
const pickStore = (st) => {
	selStoreId.value = st.id
	saveStoreId(st.id)
	storePick.value = false
	if (tableCtx.value && tableCtx.value.storeId !== st.id) {
		tableCtx.value = null
		clearTableContext()
	}
	loadProducts()
}

const setMode = (next) => {
	if (next === mode.value) return
	if (next === '外送' && tableCtx.value) {
		uni.showToast({ title: '堂食订单仅支持自取，如需外送请先取消堂食', icon: 'none' })
		return
	}
	mode.value = next
}

const dropTable = () => {
	tableCtx.value = null
	clearTableContext()
	uni.showToast({ title: '已取消堂食', icon: 'none' })
}

/** 桌号上下文生效：门店跟着切到桌码所属门店 */
const applyTable = (ctx) => {
	tableCtx.value = ctx
	saveTableContext(ctx)
	mode.value = '自取'
	storePick.value = false
	if (selStoreId.value !== ctx.storeId) {
		selStoreId.value = ctx.storeId
		saveStoreId(ctx.storeId)
		loadProducts()
	}
}

const scanTable = async () => {
	let scene = ''
	try {
		scene = await scanCode()
	} catch (error) {
		if (!isScanCancel(error)) uni.showToast({ title: '扫码失败，请重试', icon: 'none' })
		return
	}
	uni.showLoading({ title: '识别桌号…' })
	try {
		const table = await resolveTable(scene)
		uni.hideLoading()
		applyTable(table)
		uni.showToast({ title: `${table.tableNo} 桌 · ${table.storeName}`, icon: 'none' })
	} catch (error) {
		uni.hideLoading()
		showError(error)
	}
}

// 页签候选池由后端返回；classic=全部，会员/新品/常点由后端筛选
const tabDrinks = computed(() => products.value)

// 左侧 9 个分类（券包特惠置顶，NEW/HOT 角标数据驱动）
const categories = computed(() => {
	const pool = tabDrinks.value
	const lineCats = lines.value.map(l => ({
		id: l.id,
		name: l.tag + '系列',
		isNew: pool.some(d => d.line === l.id && d.isNew),
		isHot: pool.some(d => d.line === l.id && d.hot)
	}))
	return [
		{ id: 'coupon', name: '券包特惠', isNew: true },
		{ id: 'all', name: '全部饮品' }
	].concat(lineCats, [
		{ id: 'hot', name: '人气必喝', isHot: true },
		{ id: 'new', name: '新品上市' },
		{ id: 'member', name: '会员专享', isHot: true }
	])
})

const pickCategory = (id) => {
	sideId.value = id
	// 跳转动画期间锁定反写，避免滚动事件把高亮抢回上一个分类
	linkLock = Date.now() + 600
	// 重置后再设值，保证重复点同一分类也能重新跳转
	scrollInto.value = ''
	setTimeout(() => {
		scrollInto.value = id === 'all' ? (sections.value[0] ? 'sec-' + sections.value[0].id : 'sec-coupon') : 'sec-' + id
	}, 20)
}

const EXTRA_SEC = {
	hot: { name: '人气必喝', desc: '大家都在点的招牌', color: '#E8833A' },
	new: { name: '新品上市', desc: '本周新上架', color: '#E8833A' },
	member: { name: '会员专享价', desc: '会员直降，不限单', color: '#8B5E3C' }
}

// 连续分节：四条产品线常驻 + 经典页签追加人气/新品/会员汇总节，一直滑到底都有商品
const sections = computed(() => {
	const pool = tabDrinks.value
	const list = lines.value.map(l => ({
		...l,
		name: l.tag + '系列',
		drinks: pool.filter(d => d.line === l.id)
	})).filter(s => s.drinks.length)
	if (tabId.value !== 'classic') return list
	const extra = ['hot', 'new', 'member'].map(k => {
		const drinks = k === 'hot' ? pool.filter(d => d.hot)
			: k === 'new' ? pool.filter(d => d.isNew)
			: pool.filter(d => d.orig)
		return { id: k, ...EXTRA_SEC[k], drinks }
	}).filter(s => s.drinks.length)
	return list.concat(extra)
})

// ── 滚动联动：列表滑到哪里，左侧分类就跟到哪里 ──
const pageIns = getCurrentInstance()

// 量取每个分节（含券包区）相对内容顶部的偏移，滚动时据此判定当前分节
const measureSecTops = () => {
	nextTick(() => {
		const query = uni.createSelectorQuery().in(pageIns && pageIns.proxy)
		query.select('.plist').boundingClientRect()
		query.selectAll('.js-sec').boundingClientRect()
		query.exec((res) => {
			const listRect = res && res[0]
			const rects = (res && res[1]) || []
			if (!listRect || !rects.length) return
			listViewH = listRect.height
			const ids = ['sec-coupon'].concat(sections.value.map((sec) => 'sec-' + sec.id))
			const base = scrollTop.value
			secTops = rects.map((rect, index) => ({
				id: ids[index] || '',
				top: rect.top - listRect.top + base
			}))
		})
	})
}

const onListScroll = (e) => {
	const detail = e.detail
	scrollTop.value = detail.scrollTop
	if (Date.now() < linkLock || !secTops.length) return
	// 到底兜底：末尾分节顶不到判定线，滚到底部直接高亮最后一节
	if (detail.scrollHeight && detail.scrollTop + listViewH >= detail.scrollHeight - 2) {
		const lastId = secTops[secTops.length - 1].id.replace('sec-', '')
		if (lastId && lastId !== sideId.value) sideId.value = lastId
		return
	}
	// 分节顶部落过这个线，就判定为当前分节（提前 60px，滑到标题附近即切换）
	const line = detail.scrollTop + 60
	let currentId = secTops[0].id
	secTops.forEach((item) => {
		if (item.top <= line) currentId = item.id
	})
	const id = currentId.replace('sec-', '')
	if (id && id !== sideId.value) sideId.value = id
}

// 图片撑开/异步渲染后位置会变，延迟再量一次
const remeasure = () => {
	measureSecTops()
	setTimeout(measureSecTops, 350)
}

// 后端数据
const loadBase = async () => {
	const [lineList, options] = await Promise.all([getLines(), getOptions()])
	lines.value = lineList
	iceOpts.value = options.ice_options || []
	sugarOpts.value = options.sugar_options || []
	toppings.value = options.toppings || []
}
const loadStores = async () => {
	stores.value = await getStores()
	if (!stores.value.some(st => st.id === selStoreId.value) && stores.value.length) {
		selStoreId.value = stores.value[0].id
		saveStoreId(selStoreId.value)
	}
}
const loadCoupons = async () => {
	try {
		await ensureLogin().catch(() => {})
		coupons.value = await getTemplates()
	} catch (error) {
		console.warn('[menu] 券模板加载失败', error)
	}
}
const loadProducts = async () => {
	loading.value = true
	try {
		if (tabId.value === 'mine') await ensureLogin()
		const data = await getProducts({
			tab: tabId.value,
			store_id: selStoreId.value,
			page_size: 100
		})
		products.value = (data.items || []).map(toDrink)
		remeasure()
	} catch (error) {
		products.value = []
		if (tabId.value === 'mine' && error.code === 1002) {
			uni.showToast({ title: '登录后查看我的常点', icon: 'none' })
		} else {
			showError(error)
		}
	} finally {
		loading.value = false
	}
}

onMounted(async () => {
	try {
		await Promise.all([loadBase(), loadStores()])
	} catch (error) {
		showError(error)
	}
	loadCoupons()
	loadProducts()
})
// 从首页扫码回来时，onShow 同步最新的桌号上下文
onShow(() => {
	const ctx = getTableContext()
	tableCtx.value = ctx
	if (!ctx) return
	mode.value = '自取'
	if (selStoreId.value !== ctx.storeId) {
		selStoreId.value = ctx.storeId
		saveStoreId(ctx.storeId)
		loadProducts()
	}
})
// 切页签：列表重挂载并回到顶部，重新量取分节位置
watch(tabId, () => {
	scrollTop.value = 0
	remeasure()
})
// 分节数量变化（页签过滤结果不同）时也要重算
watch(() => sections.value.map((sec) => sec.id).join(','), remeasure)

// 按产品线分节，空节隐藏
const EMPTY_LINE = { id: '', name: '', tag: '', en: '', desc: '', color: '#8b5e3c', bg: '#f3eae0' }
const lineOf = (id) => lines.value.find(l => l.id === id) || EMPTY_LINE

// ===== 规格弹层 =====
const specDrink = ref(null)
const spIce = ref('正常冰')
const spSugar = ref('七分糖')
const spTops = ref([])
const spCount = ref(1)

const openSpec = (dk) => {
	specDrink.value = dk
	spIce.value = iceOpts.value.includes('正常冰') ? '正常冰' : (iceOpts.value[0] || '正常冰')
	spSugar.value = sugarOpts.value.includes('七分糖') ? '七分糖' : (sugarOpts.value[0] || '七分糖')
	spTops.value = []
	spCount.value = 1
}
const closeSpec = () => { specDrink.value = null }
const hasTop = (tp) => spTops.value.some(t => t.id === tp.id)
const toggleTop = (tp) => {
	const i = spTops.value.findIndex(t => t.id === tp.id)
	if (i > -1) spTops.value.splice(i, 1)
	else spTops.value.push(tp)
}
const spTopTotal = computed(() => spTops.value.reduce((s, t) => s + t.price, 0))
const spTotal = computed(() => (specDrink.value ? (specDrink.value.price + spTopTotal.value) * spCount.value : 0))
const spOrigTotal = computed(() => (specDrink.value && specDrink.value.orig ? specDrink.value.orig * spCount.value : 0))
const spSpecText = computed(() => [spIce.value, spSugar.value].concat(spTops.value.map(t => t.name)).join('·'))

// ===== 购物车 =====
const cart = ref([])
const cartOpen = ref(false)
const toppingTotal = (it) => (it.toppings || []).reduce((s, t) => s + Number(t.price || 0), 0)
const itemTotal = (it) => Number(((it.product.price + toppingTotal(it)) * it.count).toFixed(2))
const cartCount = computed(() => cart.value.reduce((s, it) => s + it.count, 0))
const cartTotal = computed(() => Number(cart.value.reduce((s, it) => s + itemTotal(it), 0).toFixed(2)))
const cartSave = computed(() => Number(cart.value.reduce(
	(s, it) => s + (it.product.orig ? (it.product.orig - it.product.price) * it.count : 0),
	0
).toFixed(2)))

const orderMode = () => (mode.value === '外送' ? 'delivery' : 'pickup')

const addCart = () => {
	cart.value.push({
		product: specDrink.value,
		ice: spIce.value,
		sugar: spSugar.value,
		toppings: spTops.value.slice(),
		count: spCount.value
	})
	closeSpec()
	uni.showToast({ title: '已加入购物车', icon: 'none' })
}
const buyNow = () => {
	setCheckoutDraft({
		storeId: selStoreId.value,
		mode: orderMode(),
		tableNo: tableCtx.value ? tableCtx.value.tableNo : null,
		items: [{
			product: specDrink.value,
			ice: spIce.value,
			sugar: spSugar.value,
			toppings: spTops.value.slice(),
			count: spCount.value
		}]
	})
	closeSpec()
	uni.navigateTo({ url: '/pages/checkout/index' })
}
const toggleCart = () => { cartOpen.value = !cartOpen.value }
const itemSpec = (it) => [it.ice, it.sugar].concat((it.toppings || []).map(t => t.name)).join('·')
const removeItem = (i) => {
	cart.value.splice(i, 1)
	if (!cart.value.length) cartOpen.value = false
}
const checkout = () => {
	if (!cart.value.length) return
	setCheckoutDraft({
		storeId: selStoreId.value,
		mode: orderMode(),
		tableNo: tableCtx.value ? tableCtx.value.tableNo : null,
		items: cart.value.map(it => ({
			product: it.product,
			ice: it.ice,
			sugar: it.sugar,
			toppings: it.toppings.slice(),
			count: it.count
		}))
	})
	cart.value = []
	cartOpen.value = false
	uni.navigateTo({ url: '/pages/checkout/index' })
}

const toDetail = (id) => {
	uni.navigateTo({ url: '/pages/detail/index?id=' + id + '&mode=' + (mode.value === '外送' ? 'delivery' : 'pickup') })
}
const onSearch = () => {
	uni.showToast({ title: '搜索即将上线', icon: 'none' })
}

// ===== 领券 =====
const claiming = ref(false)
const claimOne = async (cp) => {
	if (!cp || cp.claimed || claiming.value) return
	claiming.value = true
	try {
		await ensureLogin()
		await claimCoupon(cp.id)
		cp.claimed = true
		uni.showToast({ title: '领取成功', icon: 'none' })
	} catch (error) {
		if (error.code === 3003) cp.claimed = true
		showError(error)
	} finally {
		claiming.value = false
	}
}
const onClaim = (cp) => {
	claimOne(cp)
}
const claimAll = async () => {
	if (claiming.value) return
	const targets = coupons.value.filter(cp => !cp.claimed)
	if (!targets.length) {
		uni.showToast({ title: '券已全部领取', icon: 'none' })
		return
	}
	claiming.value = true
	try {
		await ensureLogin()
		for (const cp of targets) {
			try {
				await claimCoupon(cp.id)
				cp.claimed = true
			} catch (error) {
				if (error.code === 3003) cp.claimed = true
				else throw error
			}
		}
		uni.showToast({ title: '领取成功', icon: 'none' })
	} catch (error) {
		showError(error)
	} finally {
		claiming.value = false
	}
}
</script>

<style lang="scss" scoped>
.page {
	height: 100vh;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	background: #faf6f0;
}
.hv {
	opacity: 0.85;
}

/* ① 顶栏（紧凑） */
.topbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 4px 24rpx 4rpx;
}
.mode {
	display: flex;
	align-items: center;
}
.mode-t {
	font-size: 34rpx;
	font-weight: bold;
	color: #b7ab9e;
	transition: color 0.18s ease;
}
.mode-t.on {
	color: #3d3229;
}
.mode-div {
	width: 2rpx;
	height: 26rpx;
	background: #ddd2c5;
	margin: 0 20rpx;
}
.tb-actions {
	display: flex;
	align-items: center;
}
.tb-scan {
	height: 54rpx;
	padding: 0 18rpx;
	margin-right: 14rpx;
	border-radius: 999rpx;
	background: #ffffff;
	display: flex;
	align-items: center;
	box-shadow: 0 4rpx 12rpx rgba(61, 50, 41, 0.06);
}
.tb-scan-t {
	font-size: 24rpx;
	font-weight: bold;
	color: #8b5e3c;
}
.tb-search {
	width: 54rpx;
	height: 54rpx;
	border-radius: 50%;
	background: #ffffff;
	display: flex;
	align-items: center;
	justify-content: center;
	box-shadow: 0 4rpx 12rpx rgba(61, 50, 41, 0.06);
}

/* 堂食桌号条 */
.table-bar {
	display: flex;
	align-items: center;
	margin: 4rpx 24rpx 6rpx;
	padding: 10rpx 16rpx;
	border-radius: 14rpx;
	background: #fdf1e4;
}
.tb-tag {
	flex-shrink: 0;
	padding: 2rpx 10rpx;
	border-radius: 8rpx;
	background: #e8833a;
	font-size: 20rpx;
	color: #ffffff;
}
.tbb-name {
	flex: 1;
	min-width: 0;
	margin-left: 12rpx;
	font-size: 22rpx;
	color: #8c8177;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.tbb-no {
	flex-shrink: 0;
	margin-left: 8rpx;
	font-size: 24rpx;
	font-weight: bold;
	color: #8b5e3c;
}
.tbb-clear {
	flex-shrink: 0;
	margin-left: 16rpx;
	font-size: 22rpx;
	color: #b7ab9e;
}

/* ② 门店行（紧凑） */
.store-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 4rpx 24rpx 6rpx;
}
.st-left {
	flex: 1;
	min-width: 0;
}
.st-name {
	display: flex;
	align-items: center;
	min-width: 0;
}
.st-title {
	flex: 1;
	min-width: 0;
	margin: 0 6rpx 0 8rpx;
	font-size: 29rpx;
	font-weight: bold;
	color: #3d3229;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}
.st-arrow {
	flex-shrink: 0;
	font-size: 28rpx;
	color: #8c8177;
}
.st-meta {
	display: flex;
	align-items: center;
	margin-top: 4rpx;
}
.st-dist-t {
	font-size: 20rpx;
	color: #8c8177;
}
.st-dot {
	margin: 0 8rpx;
	font-size: 20rpx;
	color: #c9c0b7;
}
.st-status {
	font-size: 20rpx;
	color: #8c8177;
}
.st-live {
	display: flex;
	align-items: center;
	margin-left: 12rpx;
	padding: 2rpx 10rpx;
	border-radius: 999rpx;
	background: #eaf3ec;
}
.st-live-dot {
	width: 8rpx;
	height: 8rpx;
	border-radius: 50%;
	background: #5c9e6e;
	margin-right: 6rpx;
}
.st-live-t {
	font-size: 18rpx;
	color: #5c9e6e;
}
.st-badge {
	flex-shrink: 0;
	margin-left: 16rpx;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	width: 74rpx;
	height: 74rpx;
	border-radius: 18rpx 18rpx 18rpx 4rpx;
	background: #f3eae0;
}
.stb-t1 {
	font-size: 20rpx;
	font-weight: bold;
	color: #8b5e3c;
}
.stb-t2 {
	font-size: 16rpx;
	color: #8b5e3c;
	margin-top: 2rpx;
}

/* ③ 券包卡（券包特惠分类） */
.cp-head {
	display: flex;
	align-items: baseline;
	padding: 20rpx 4rpx 12rpx;
	margin: 0 16rpx;
}
.cp-h-t {
	font-size: 27rpx;
	font-weight: bold;
	color: #3d3229;
}
.cp-h-s {
	margin-left: 12rpx;
	font-size: 20rpx;
	color: #b7ab9e;
}
/* 券包卡片样式见 components/menu/coupon-ticket.vue */

/* ④ 新客 banner（随列表滚动） */
.promo-banner {
	position: relative;
	margin: 16rpx 16rpx 6rpx;
	padding: 18rpx 22rpx;
	border-radius: 22rpx;
	background: linear-gradient(120deg, #fdeedc 0%, #f9dcb8 58%, #f6cf9e 100%);
	overflow: hidden;
}
.pb-deco {
	position: absolute;
	border-radius: 50%;
}
.pb-d1 {
	right: -40rpx;
	top: -50rpx;
	width: 170rpx;
	height: 170rpx;
	background: rgba(255, 255, 255, 0.45);
}
.pb-d2 {
	right: 80rpx;
	bottom: -60rpx;
	width: 120rpx;
	height: 120rpx;
	background: rgba(232, 131, 58, 0.14);
}
.pb-left {
	position: relative;
}
.pb-tag {
	display: inline-block;
	padding: 2rpx 12rpx;
	border-radius: 8rpx;
	background: #8b5e3c;
	color: #fff7ec;
	font-size: 18rpx;
}
.pb-title {
	display: flex;
	align-items: baseline;
	margin-top: 8rpx;
}
.pb-big {
	font-size: 34rpx;
	font-weight: 900;
	color: #5a3a1e;
	letter-spacing: 1rpx;
}
.pb-sub2 {
	display: block;
	margin-top: 6rpx;
	font-size: 20rpx;
	color: #8b5e3c;
}
.pb-btn {
	display: inline-block;
	margin-top: 10rpx;
	padding: 6rpx 24rpx;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 4rpx 12rpx rgba(232, 131, 58, 0.35);
	color: #ffffff;
	font-size: 22rpx;
	font-weight: 500;
}

/* ⑤ 页签（紧凑） */
.mtabs {
	display: flex;
	padding: 0 24rpx;
	border-bottom: 2rpx solid #f0e7da;
	background: #faf6f0;
}
.mt-tab {
	margin-right: 44rpx;
	padding: 8rpx 0 0;
	display: flex;
	flex-direction: column;
	align-items: center;
}
.mt-t {
	font-size: 26rpx;
	color: #8c8177;
	padding-bottom: 10rpx;
}
.mt-tab.on .mt-t {
	font-size: 28rpx;
	font-weight: bold;
	color: #3d3229;
}
.mt-bar {
	width: 40rpx;
	height: 6rpx;
	border-radius: 3rpx;
	background: transparent;
}
.mt-tab.on .mt-bar {
	background: #8b5e3c;
}

/* ⑥ 分类 + 列表（占据剩余全部高度） */
.content {
	flex: 1;
	min-height: 0;
	display: flex;
}
/* 左侧分类样式见 components/menu/category-rail.vue */

.plist {
	flex: 1;
	height: 100%;
	/* 不给 scroll-view 横向 padding：小程序里会被 100% 宽的子内容顶掉导致溢出裁切，间距全部用子元素 margin 实现 */
}
.no-drink {
	margin: 0 20rpx;
	padding: 60rpx 0;
	text-align: center;
	font-size: 24rpx;
	color: #b7ab9e;
}
.sec-head {
	display: flex;
	align-items: baseline;
	padding: 22rpx 4rpx 14rpx;
	margin: 0 12rpx;
}
.sec-name {
	font-size: 28rpx;
	font-weight: bold;
}
.sec-desc {
	margin-left: 12rpx;
	font-size: 20rpx;
	color: #b7ab9e;
}
/* 商品卡布局见 components/menu/product-card.vue，价格样式下方保留给规格弹层复用 */
.p-price {
	display: flex;
	align-items: baseline;
	color: #e8833a;
}
.p-sym {
	font-size: 24rpx;
	font-weight: bold;
}
.p-num {
	font-size: 44rpx;
	font-weight: bold;
}
.p-orig {
	margin-left: 10rpx;
	font-size: 21rpx;
	color: #b7ab9e;
	text-decoration: line-through;
}

/* ⑦ 购物车栏：底部渐隐垫层，商品卡从后面淡出，不再露出被截断的半截卡片 */
.cart-wrap {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 60;
	padding: 20rpx 24rpx 24rpx;
	background: linear-gradient(180deg, rgba(250, 246, 240, 0) 0%, rgba(250, 246, 240, 0.94) 40%, #faf6f0 100%);
}
/* 明细展开时的轻遮罩：压暗列表，购物车条仍可点收起 */
.mask.cart-mask {
	z-index: 55;
	background: rgba(30, 24, 18, 0.38);
}
.cart-tip {
	text-align: center;
	margin-bottom: 12rpx;
}
.cart-save {
	display: inline-block;
	padding: 6rpx 22rpx;
	border-radius: 999rpx;
	background: #f7ecd9;
	color: #9a7a5c;
	font-size: 20rpx;
	line-height: 1.5;
}
.cb-chev {
	width: 14rpx;
	height: 14rpx;
	margin-left: 16rpx;
	border-left: 3rpx solid #a99c8f;
	border-top: 3rpx solid #a99c8f;
	transform: rotate(45deg) translateY(3rpx);
	transition: transform 0.2s ease;
}
.cb-chev.open {
	transform: rotate(225deg) translateY(3rpx);
}
/* 展开的已选明细：白卡浮在购物车条上方 */
.cart-panel {
	margin-bottom: 14rpx;
	padding: 24rpx 24rpx 8rpx;
	background: #ffffff;
	border-radius: 28rpx;
	box-shadow: 0 8rpx 28rpx rgba(61, 50, 41, 0.1);
	animation: slideUp 0.22s ease both;
}
.cpn-head {
	display: flex;
	align-items: baseline;
	justify-content: space-between;
	padding: 0 4rpx 16rpx;
	border-bottom: 2rpx solid #f5efe7;
}
.cpn-t {
	font-size: 26rpx;
	font-weight: bold;
	color: #3d3229;
}
.cpn-s {
	font-size: 20rpx;
	color: #a99c8f;
}
.cpn-list {
	max-height: 480rpx;
}
.cpn-item {
	display: flex;
	align-items: center;
	padding: 20rpx 0;
	border-bottom: 2rpx solid #f7f2ea;
}
.cpn-item:last-child {
	border-bottom: none;
}
.cpn-img {
	flex-shrink: 0;
	width: 84rpx;
	height: 84rpx;
	border-radius: 18rpx;
	background: #f3ece2;
}
.cpn-mid {
	flex: 1;
	min-width: 0;
	margin-left: 18rpx;
	display: flex;
	flex-direction: column;
}
.cpn-name {
	font-size: 26rpx;
	font-weight: 500;
	color: #3d3229;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}
.cpn-spec {
	margin-top: 6rpx;
	font-size: 20rpx;
	color: #a99c8f;
	overflow: hidden;
	white-space: nowrap;
	text-overflow: ellipsis;
}
.cpn-right {
	flex-shrink: 0;
	margin-left: 14rpx;
	display: flex;
	flex-direction: column;
	align-items: flex-end;
}
.cpn-price {
	font-size: 26rpx;
	font-weight: bold;
	color: #e8833a;
}
.cpn-count {
	margin-top: 4rpx;
	font-size: 20rpx;
	color: #a99c8f;
}
.cpn-del {
	flex-shrink: 0;
	margin-left: 18rpx;
	padding: 8rpx 18rpx;
	border-radius: 999rpx;
	border: 2rpx solid #eee7de;
	font-size: 20rpx;
	color: #a99c8f;
}
.cart-bar {
	display: flex;
	align-items: center;
	height: 100rpx;
	padding-left: 10rpx;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #4a3b2e 0%, #332a22 100%);
	box-shadow: 0 10rpx 26rpx rgba(61, 50, 41, 0.18);
}
.cb-left {
	flex: 1;
	display: flex;
	align-items: center;
	padding-left: 12rpx;
}
.cb-icon {
	position: relative;
	width: 68rpx;
	height: 68rpx;
	border-radius: 50%;
	background: rgba(255, 247, 236, 0.12);
	display: flex;
	align-items: center;
	justify-content: center;
}
.cb-badge {
	position: absolute;
	top: -6rpx;
	right: -6rpx;
	min-width: 30rpx;
	height: 30rpx;
	line-height: 30rpx;
	padding: 0 6rpx;
	border-radius: 15rpx;
	background: #e8833a;
	color: #ffffff;
	font-size: 18rpx;
	font-weight: bold;
	text-align: center;
}
.cb-price {
	display: flex;
	align-items: baseline;
	margin-left: 18rpx;
	color: #fff7ec;
}
.cb-pre {
	font-size: 20rpx;
	color: #a99c8f;
	margin-right: 6rpx;
}
.cb-sym {
	font-size: 22rpx;
	font-weight: bold;
}
.cb-num {
	font-size: 36rpx;
	font-weight: bold;
}
.cb-orig {
	margin-left: 10rpx;
	font-size: 20rpx;
	color: #857769;
	text-decoration: line-through;
}
.cb-go {
	flex-shrink: 0;
	height: 80rpx;
	line-height: 80rpx;
	margin: 10rpx;
	padding: 0 40rpx;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 6rpx 14rpx rgba(232, 131, 58, 0.28);
	color: #ffffff;
	font-size: 27rpx;
	font-weight: 600;
}

/* 弹层通用 */
.mask {
	position: fixed;
	left: 0;
	top: 0;
	right: 0;
	bottom: 0;
	background: rgba(30, 24, 18, 0.55);
	z-index: 90;
	animation: fadeIn 0.22s ease both;
}
@keyframes fadeIn {
	from { opacity: 0; }
	to { opacity: 1; }
}
@keyframes slideUp {
	from { transform: translateY(60rpx); opacity: 0; }
	to { transform: translateY(0); opacity: 1; }
}

/* ⑧ 地图选店弹层 */
.store-sheet {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 100;
	background: #ffffff;
	border-radius: 32rpx 32rpx 0 0;
	padding: 16rpx 32rpx 0;
	animation: slideUp 0.28s cubic-bezier(0.32, 0.72, 0.4, 1) both;
}
.ss-handle {
	width: 72rpx;
	height: 8rpx;
	border-radius: 4rpx;
	background: #e6dccc;
	margin: 0 auto 18rpx;
}
.ss-title {
	display: block;
	text-align: center;
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}
.ss-map {
	position: relative;
	height: 260rpx;
	border-radius: 20rpx;
	background: #f1ebe1;
	overflow: hidden;
	margin: 20rpx 0 8rpx;
}
.ss-block {
	position: absolute;
	border-radius: 12rpx;
	background: #e6dcc8;
}
.ss-b1 {
	left: -30rpx;
	top: -40rpx;
	width: 220rpx;
	height: 180rpx;
}
.ss-b2 {
	right: -40rpx;
	top: 30rpx;
	width: 260rpx;
	height: 200rpx;
	background: #e2f0e4;
}
.ss-b3 {
	left: 60rpx;
	bottom: -60rpx;
	width: 300rpx;
	height: 160rpx;
}
.ss-road {
	position: absolute;
	background: #ffffff;
	border-radius: 8rpx;
}
.ss-r1 {
	left: -20rpx;
	right: -20rpx;
	top: 40%;
	height: 26rpx;
	transform: rotate(-4deg);
}
.ss-r2 {
	top: -20rpx;
	bottom: -20rpx;
	left: 58%;
	width: 26rpx;
	transform: rotate(6deg);
}
.ss-pin {
	position: absolute;
	left: 46%;
	top: 24%;
}
.ss-pin-dot {
	width: 36rpx;
	height: 36rpx;
	border-radius: 50% 50% 50% 0;
	background: #e8833a;
	transform: rotate(-45deg);
	box-shadow: 0 6rpx 16rpx rgba(232, 131, 58, 0.5);
	border: 4rpx solid #ffffff;
}
.ss-bubble {
	position: absolute;
	left: 30rpx;
	top: -34rpx;
	padding: 6rpx 16rpx;
	border-radius: 999rpx;
	background: #3d3229;
	color: #fff7ec;
	font-size: 20rpx;
	white-space: nowrap;
}
.ss-item {
	display: flex;
	align-items: center;
	padding: 24rpx 4rpx;
	border-bottom: 2rpx solid #f5efe7;
}
.ss-radio {
	flex-shrink: 0;
	width: 32rpx;
	height: 32rpx;
	border-radius: 50%;
	border: 4rpx solid #ddd2c5;
	box-sizing: border-box;
	transition: all 0.18s ease;
}
.ss-radio.on {
	border: 10rpx solid #e8833a;
}
.ss-mid {
	flex: 1;
	min-width: 0;
	margin-left: 20rpx;
}
.ss-name {
	display: block;
	font-size: 27rpx;
	font-weight: bold;
	color: #3d3229;
}
.ss-area {
	display: block;
	margin-top: 4rpx;
	font-size: 20rpx;
	color: #8c8177;
}
.ss-cur {
	flex-shrink: 0;
	font-size: 20rpx;
	color: #e8833a;
	font-weight: bold;
}
.ss-pad {
	height: calc(24rpx + env(safe-area-inset-bottom));
}

/* ⑨ 规格弹层 */
.spec-sheet {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	z-index: 100;
	display: flex;
	flex-direction: column;
	max-height: 82vh;
	background: #ffffff;
	border-radius: 32rpx 32rpx 0 0;
	overflow: hidden;
	animation: slideUp 0.28s cubic-bezier(0.32, 0.72, 0.4, 1) both;
}
.sp-hero {
	position: relative;
	height: 320rpx;
	display: flex;
	align-items: center;
	justify-content: center;
	flex-shrink: 0;
}
.sp-img {
	width: 250rpx;
	height: 250rpx;
	border-radius: 24rpx;
	box-shadow: 0 16rpx 40rpx rgba(61, 50, 41, 0.18);
}
.sp-close {
	position: absolute;
	right: 28rpx;
	top: 24rpx;
	width: 56rpx;
	height: 56rpx;
	border-radius: 50%;
	background: rgba(61, 50, 41, 0.4);
	display: flex;
	align-items: center;
	justify-content: center;
}
.sp-info {
	padding: 20rpx 32rpx 6rpx;
	flex-shrink: 0;
}
.sp-name-row {
	display: flex;
	align-items: center;
}
.sp-name {
	font-size: 34rpx;
	font-weight: bold;
	color: #3d3229;
}
.sp-ltag {
	margin-left: 14rpx;
	padding: 2rpx 14rpx;
	border-radius: 8rpx;
	font-size: 19rpx;
}
.sp-desc {
	display: block;
	margin-top: 8rpx;
	font-size: 22rpx;
	color: #8c8177;
}
.sp-opts {
	flex: 1;
	min-height: 0;
	/* 同 plist：scroll-view 不加横向 padding，间距用子元素 margin */
}
.sp-group {
	padding: 18rpx 0 4rpx;
	margin: 0 32rpx;
}
.sp-gtitle {
	display: block;
	font-size: 25rpx;
	font-weight: bold;
	color: #3d3229;
}
.sp-gsub {
	font-size: 20rpx;
	font-weight: normal;
	color: #b7ab9e;
}
.sp-chips {
	display: flex;
	flex-wrap: wrap;
	gap: 16rpx;
	margin-top: 14rpx;
}
.sp-chip {
	padding: 10rpx 28rpx;
	border-radius: 12rpx;
	background: #f5efe7;
	color: #5a4f43;
	font-size: 23rpx;
	border: 2rpx solid transparent;
	transition: all 0.16s ease;
}
.sp-chip.on {
	background: #fdeedd;
	border-color: #e8833a;
	color: #e8833a;
	font-weight: bold;
}
.sp-foot {
	flex-shrink: 0;
	padding: 16rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
	border-top: 2rpx solid #f5efe7;
}
.sp-price-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
}
.sp-count {
	display: flex;
	align-items: center;
}
.sc-btn {
	width: 52rpx;
	height: 52rpx;
	line-height: 48rpx;
	text-align: center;
	border-radius: 50%;
	background: #f5efe7;
	color: #5a4f43;
	font-size: 30rpx;
}
.sc-add {
	background: #e8833a;
	color: #ffffff;
}
.sc-num {
	min-width: 64rpx;
	text-align: center;
	font-size: 28rpx;
	font-weight: bold;
	color: #3d3229;
}
.sp-sum {
	display: block;
	margin-top: 10rpx;
	font-size: 20rpx;
	color: #8c8177;
}
.sp-btns {
	display: flex;
	gap: 20rpx;
	margin-top: 18rpx;
}
.sp-buy {
	flex: 1;
	height: 84rpx;
	line-height: 84rpx;
	text-align: center;
	border-radius: 999rpx;
	border: 2rpx solid #8b5e3c;
	color: #8b5e3c;
	font-size: 27rpx;
	font-weight: bold;
	box-sizing: border-box;
}
.sp-addcart {
	flex: 1.6;
	height: 84rpx;
	line-height: 84rpx;
	text-align: center;
	border-radius: 999rpx;
	background: linear-gradient(135deg, #f09a52 0%, #e8833a 100%);
	box-shadow: 0 8rpx 20rpx rgba(232, 131, 58, 0.35);
	color: #ffffff;
	font-size: 27rpx;
	font-weight: bold;
}
.list-pad {
	height: 60rpx;
}
.list-pad.withCart {
	height: 250rpx;
}
</style>
