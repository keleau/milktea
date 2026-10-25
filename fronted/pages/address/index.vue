<template>
	<view class="page">
		<text class="tip" v-if="selectMode">点击地址卡片即可用于本次配送</text>

		<view class="addr-list" v-if="addresses.length">
			<view class="addr-card" v-for="addr in addresses" :key="addr.id" hover-class="hv" @tap="choose(addr)">
				<view class="ac-top">
					<text class="ac-name">{{ addr.name }}</text>
					<text class="ac-phone">{{ addr.phone }}</text>
					<text class="ac-tag" v-if="addr.is_default">默认</text>
				</view>
				<text class="ac-detail">{{ addr.detail }}</text>
				<view class="ac-actions">
					<text class="ac-act" v-if="!addr.is_default" @tap.stop="markDefault(addr)">设为默认</text>
					<text class="ac-act" @tap.stop="openEdit(addr)">编辑</text>
					<text class="ac-act danger" @tap.stop="remove(addr)">删除</text>
				</view>
			</view>
		</view>

		<view class="empty" v-else-if="!loading">
			<text class="empty-title">还没有收货地址</text>
			<text class="empty-sub">新增后外送下单会默认使用它</text>
		</view>
		<view class="loading" v-else>加载中…</view>

		<view class="fix-space"></view>
		<view class="fix-bar">
			<view class="add-btn" hover-class="hv" @tap="openCreate">+ 新增收货地址</view>
		</view>

		<!-- 新增/编辑弹层 -->
		<view class="form-mask" v-if="formOpen" @tap="formOpen = false">
			<view class="form-card" @tap.stop>
				<text class="form-title">{{ editingId ? '编辑地址' : '新增地址' }}</text>
				<view class="field">
					<text class="f-label">收货人</text>
					<input class="f-input" v-model="form.name" maxlength="20" placeholder="请输入姓名" />
				</view>
				<view class="field">
					<text class="f-label">手机号</text>
					<input class="f-input" v-model="form.phone" type="number" maxlength="11" placeholder="请输入 11 位手机号" />
				</view>
				<view class="field">
					<text class="f-label">详细地址</text>
					<input class="f-input" v-model="form.detail" maxlength="120" placeholder="小区、楼栋、门牌号" />
				</view>
				<view class="field switch-field">
					<text class="f-label">设为默认</text>
					<switch :checked="form.is_default" color="#8B5E3C" @change="onDefaultChange" />
				</view>
				<view class="form-actions">
					<view class="f-cancel" hover-class="hv" @tap="formOpen = false">取消</view>
					<view class="f-submit" hover-class="hv" @tap="submitForm">{{ saving ? '保存中…' : '保存' }}</view>
				</view>
			</view>
		</view>
	</view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import {
	createAddress,
	deleteAddress,
	getAddresses,
	setDefaultAddress,
	updateAddress
} from '@/common/api/addresses'
import { ensureLogin } from '@/common/api/auth'
import { showError } from '@/common/api/request'
import { setSelectedAddressId } from '@/common/store/session'

const addresses = ref([])
const loading = ref(true)
const selectMode = ref(false)
const formOpen = ref(false)
const editingId = ref(0)
const saving = ref(false)
const form = ref({ name: '', phone: '', detail: '', is_default: false })

onLoad((params) => {
	selectMode.value = params.select === '1'
})

onShow(() => {
	loadList()
})

const loadList = async () => {
	loading.value = true
	try {
		await ensureLogin()
		addresses.value = await getAddresses()
	} catch (error) {
		showError(error)
	} finally {
		loading.value = false
	}
}

const choose = (addr) => {
	if (!selectMode.value) return
	setSelectedAddressId(addr.id)
	uni.navigateBack()
}

const openCreate = () => {
	editingId.value = 0
	form.value = { name: '', phone: '', detail: '', is_default: !addresses.value.length }
	formOpen.value = true
}

const openEdit = (addr) => {
	editingId.value = addr.id
	form.value = {
		name: addr.name,
		phone: addr.phone,
		detail: addr.detail,
		is_default: addr.is_default
	}
	formOpen.value = true
}

const onDefaultChange = (event) => {
	form.value.is_default = event.detail.value
}

const submitForm = async () => {
	if (saving.value) return
	const name = form.value.name.trim()
	const phone = form.value.phone.trim()
	const detail = form.value.detail.trim()
	if (!name) {
		uni.showToast({ title: '请填写收货人', icon: 'none' })
		return
	}
	if (!/^1[3-9]\d{9}$/.test(phone)) {
		uni.showToast({ title: '手机号格式不正确', icon: 'none' })
		return
	}
	if (!detail) {
		uni.showToast({ title: '请填写详细地址', icon: 'none' })
		return
	}

	saving.value = true
	try {
		const payload = { name, phone, detail, is_default: form.value.is_default }
		if (editingId.value) {
			await updateAddress(editingId.value, payload)
		} else {
			await createAddress(payload)
		}
		formOpen.value = false
		uni.showToast({ title: '已保存', icon: 'success' })
		await loadList()
	} catch (error) {
		showError(error)
	} finally {
		saving.value = false
	}
}

const markDefault = async (addr) => {
	try {
		await setDefaultAddress(addr.id)
		await loadList()
		uni.showToast({ title: '已设为默认', icon: 'none' })
	} catch (error) {
		showError(error)
	}
}

const remove = (addr) => {
	uni.showModal({
		title: '删除地址',
		content: `确定删除 ${addr.name} 的地址？`,
		success: async (res) => {
			if (!res.confirm) return
			try {
				await deleteAddress(addr.id)
				await loadList()
				uni.showToast({ title: '已删除', icon: 'none' })
			} catch (error) {
				showError(error)
			}
		}
	})
}
</script>

<style>
page {
	background: #faf6f0;
}
.page {
	min-height: 100vh;
	padding: 24rpx 32rpx 0;
	box-sizing: border-box;
}
.hv {
	opacity: 0.85;
}
.tip {
	display: block;
	font-size: 24rpx;
	color: #a79b8e;
	margin-bottom: 16rpx;
}
.addr-card {
	background: #ffffff;
	border-radius: 32rpx;
	padding: 28rpx 28rpx 20rpx;
	margin-bottom: 20rpx;
	box-shadow: 0 8rpx 24rpx rgba(61, 50, 41, 0.06);
}
.ac-top {
	display: flex;
	align-items: center;
}
.ac-name {
	font-size: 30rpx;
	font-weight: bold;
	color: #3d3229;
}
.ac-phone {
	margin-left: 16rpx;
	font-size: 26rpx;
	color: #6f6258;
}
.ac-tag {
	margin-left: 12rpx;
	font-size: 20rpx;
	color: #e8833a;
	border: 2rpx solid #f0c9a8;
	border-radius: 8rpx;
	padding: 2rpx 10rpx;
}
.ac-detail {
	display: block;
	margin-top: 14rpx;
	font-size: 26rpx;
	line-height: 1.6;
	color: #8c8177;
}
.ac-actions {
	display: flex;
	justify-content: flex-end;
	margin-top: 16rpx;
	padding-top: 16rpx;
	border-top: 2rpx solid #f0e9e1;
}
.ac-act {
	font-size: 24rpx;
	color: #6f6258;
	margin-left: 32rpx;
}
.ac-act.danger {
	color: #c96b57;
}

/* 空态 / 加载 */
.empty {
	padding: 200rpx 0;
	display: flex;
	flex-direction: column;
	align-items: center;
}
.empty-title {
	font-size: 30rpx;
	color: #6f6258;
}
.empty-sub {
	margin-top: 12rpx;
	font-size: 24rpx;
	color: #b7ab9e;
}
.loading {
	padding: 200rpx 0;
	text-align: center;
	font-size: 26rpx;
	color: #a79b8e;
}

/* 底部按钮 */
.fix-space {
	height: 140rpx;
}
.fix-bar {
	position: fixed;
	left: 0;
	right: 0;
	bottom: 0;
	padding: 20rpx 32rpx calc(20rpx + env(safe-area-inset-bottom));
	background: #ffffff;
	box-shadow: 0 -8rpx 24rpx rgba(61, 50, 41, 0.08);
}
.add-btn {
	height: 88rpx;
	line-height: 88rpx;
	text-align: center;
	background: #8b5e3c;
	color: #ffffff;
	font-size: 30rpx;
	border-radius: 44rpx;
}

/* 表单弹层 */
.form-mask {
	position: fixed;
	left: 0;
	right: 0;
	top: 0;
	bottom: 0;
	background: rgba(40, 32, 26, 0.45);
	display: flex;
	align-items: flex-end;
	z-index: 20;
}
.form-card {
	width: 100%;
	background: #ffffff;
	border-radius: 40rpx 40rpx 0 0;
	padding: 36rpx 40rpx calc(32rpx + env(safe-area-inset-bottom));
	box-sizing: border-box;
}
.form-title {
	display: block;
	text-align: center;
	font-size: 32rpx;
	font-weight: bold;
	color: #3d3229;
	margin-bottom: 24rpx;
}
.field {
	display: flex;
	align-items: center;
	padding: 22rpx 0;
	border-bottom: 2rpx solid #f0e9e1;
}
.f-label {
	width: 150rpx;
	font-size: 28rpx;
	color: #6f6258;
}
.f-input {
	flex: 1;
	font-size: 28rpx;
	color: #3d3229;
}
.switch-field {
	justify-content: space-between;
	border-bottom: none;
}
.form-actions {
	display: flex;
	margin-top: 24rpx;
}
.f-cancel,
.f-submit {
	flex: 1;
	height: 84rpx;
	line-height: 84rpx;
	text-align: center;
	border-radius: 42rpx;
	font-size: 28rpx;
}
.f-cancel {
	margin-right: 20rpx;
	background: #f3ece3;
	color: #6f6258;
}
.f-submit {
	background: #8b5e3c;
	color: #ffffff;
}
</style>
