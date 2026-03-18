<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import {
    adminReviewApi,
    type AdminReviewListItem,
    type AdminReviewDetail,
    type AdminPageResponse,
} from '@/api/client'
import { formatRelativeTime } from '@/composables/useActivityFeed'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { TooltipProvider } from '@/components/ui/tooltip'
import {
    Search,
    RefreshCw,
    Loader2,
    AlertCircle,
    ClipboardCheck,
    ArrowLeft,
    ArrowRight,
    CheckCircle2,
    XCircle,
} from 'lucide-vue-next'

// ─── 状态 ───

const PAGE_SIZE = 20

const keyword = ref('')
const resultFilter = ref('all')
const page = ref(1)

const loading = ref(false)
const loadingDetail = ref(false)
const listError = ref('')
const detailError = ref('')

const selectedReviewId = ref<string | null>(null)
const selectedReview = ref<AdminReviewDetail | null>(null)

const pageData = ref<AdminPageResponse<AdminReviewListItem>>(createEmptyPage())

let listRequestId = 0
let detailRequestId = 0
const detailKey = ref(0)

// ─── 选项 ───

const resultOptions = [
    { value: 'all', label: '全部结果' },
    { value: 'approved', label: '✅ 通过' },
    { value: 'rejected', label: '❌ 驳回' },
]

// ─── 工具函数 ───

function createEmptyPage<T = unknown>(): AdminPageResponse<T> {
    return { items: [] as T[], total: 0, page: 1, page_size: PAGE_SIZE, total_pages: 1, has_more: false }
}

function formatDate(value: string | null) {
    if (!value) return '—'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return '—'
    return new Intl.DateTimeFormat('zh-CN', {
        month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
    }).format(date)
}


function scoreStars(score: number) {
    return '★'.repeat(Math.max(0, Math.min(5, score))) + '☆'.repeat(Math.max(0, 5 - score))
}

// ─── 数据加载 ───

const reloadDebounced = useDebounceFn(() => {
    page.value = 1
    void loadList()
}, 280)

watch([keyword, resultFilter], () => {
    loading.value = true
    reloadDebounced()
})

onMounted(() => {
    void loadList()
})

async function loadList() {
    const rid = ++listRequestId
    loading.value = true
    listError.value = ''

    try {
        const response = await adminReviewApi.list({
            page: page.value,
            page_size: PAGE_SIZE,
            keyword: keyword.value.trim() || undefined,
            result: resultFilter.value === 'all' ? undefined : resultFilter.value,
            sort_order: 'desc',
        })
        if (rid !== listRequestId) return
        pageData.value = response.data

        const firstItem = response.data.items[0]
        if (!firstItem) {
            selectedReviewId.value = null
            selectedReview.value = null
            return
        }
        const currentIds = new Set(response.data.items.map(i => i.id))
        const nextId =
            selectedReviewId.value && currentIds.has(selectedReviewId.value)
                ? selectedReviewId.value
                : firstItem.id
        if (nextId !== selectedReviewId.value) {
            selectedReviewId.value = nextId
            void loadDetail(nextId)
        }
    } catch (e) {
        if (rid !== listRequestId) return
        console.error('Failed to load reviews', e)
        listError.value = '审查记录加载失败，请重试。'
    } finally {
        if (rid === listRequestId) loading.value = false
    }
}

async function loadDetail(reviewId: string) {
    const rid = ++detailRequestId
    loadingDetail.value = true
    detailError.value = ''

    try {
        const response = await adminReviewApi.get(reviewId)
        if (rid !== detailRequestId || selectedReviewId.value !== reviewId) return
        selectedReview.value = response.data
        detailKey.value++
    } catch (e) {
        if (rid !== detailRequestId) return
        console.error('Failed to load review detail', e)
        detailError.value = '详情加载失败，请重试。'
        selectedReview.value = null
    } finally {
        if (rid === detailRequestId) loadingDetail.value = false
    }
}

function selectReview(id: string) {
    if (selectedReviewId.value === id) return
    selectedReviewId.value = id
    void loadDetail(id)
}

function goToPage(p: number) {
    if (p < 1 || p > pageData.value.total_pages || p === page.value) return
    page.value = p
    void loadList()
}
</script>

<template>
    <TooltipProvider>
        <div class="flex flex-col h-[calc(100vh-3.5rem)]">
            <!-- ─── 顶栏 ─── -->
            <header class="shrink-0 border-b border-border/40 bg-background px-4 py-3 space-y-2.5">
                <div class="flex items-center gap-3">
                    <div class="relative flex-1 max-w-sm">
                        <Search
                            class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                        <Input v-model="keyword" class="h-9 bg-muted/30 pl-10 text-sm" placeholder="搜索任务名、子任务名、审查意见…" />
                    </div>

                    <Badge variant="secondary" class="h-7 px-2.5 text-xs tabular-nums shrink-0">
                        {{ pageData.total }} 条
                    </Badge>

                    <Button variant="ghost" size="icon" class="h-8 w-8 shrink-0" :disabled="loading" @click="loadList">
                        <RefreshCw class="h-3.5 w-3.5" :class="loading ? 'animate-spin' : ''" />
                    </Button>
                </div>

                <!-- 结果筛选 -->
                <div class="flex items-center gap-1.5">
                    <Button v-for="option in resultOptions" :key="option.value" size="sm"
                        :variant="resultFilter === option.value ? 'default' : 'ghost'"
                        class="h-7 rounded-full px-3 text-xs" @click="resultFilter = option.value">
                        {{ option.label }}
                    </Button>
                </div>
            </header>

            <!-- ─── 主内容：左右分栏 ─── -->
            <div class="flex flex-1 min-h-0">
                <!-- 左栏：列表 -->
                <div class="w-[380px] shrink-0 border-r border-border/30 flex flex-col">
                    <!-- 列表错误 -->
                    <div v-if="listError" class="flex flex-col items-center justify-center flex-1">
                        <AlertCircle class="h-5 w-5 text-muted-foreground" />
                        <p class="mt-2 text-sm">{{ listError }}</p>
                        <Button class="mt-3" size="sm" @click="loadList">重新加载</Button>
                    </div>

                    <!-- 加载中 -->
                    <div v-else-if="loading" class="flex items-center justify-center flex-1">
                        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>

                    <!-- 列表 -->
                    <template v-else>
                        <div class="flex-1 overflow-y-auto">
                            <div v-if="pageData.items.length" class="divide-y divide-border/20">
                                <button v-for="(review, idx) in pageData.items" :key="review.id" type="button"
                                    class="w-full text-left px-4 py-3 hover:bg-muted/30 transition-all cursor-pointer animate-slide-up"
                                    :class="selectedReviewId === review.id ? 'bg-muted/40 border-l-2 border-l-primary' : 'border-l-2 border-l-transparent'"
                                    :style="{ animationDelay: `${idx * 25}ms` }" @click="selectReview(review.id)">
                                    <!-- 第一行：结果 + 子任务名 + 时间 -->
                                    <div class="flex items-center gap-1.5">
                                        <CheckCircle2 v-if="review.result === 'approved'"
                                            class="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                                        <XCircle v-else class="h-3.5 w-3.5 text-rose-500 shrink-0" />
                                        <span class="text-sm font-medium truncate flex-1">{{
                                            review.sub_task_name }}</span>
                                        <span class="text-[10px] text-muted-foreground/50 shrink-0 tabular-nums">
                                            {{ formatRelativeTime(review.created_at) }}
                                        </span>
                                    </div>
                                    <!-- 第二行：评分 + reviewer + 轮次 -->
                                    <div class="flex items-center gap-2 mt-1 text-[11px] text-muted-foreground">
                                        <span class="text-amber-500">{{ scoreStars(review.score) }}</span>
                                        <span>{{ review.reviewer_agent_name || '未知' }}</span>
                                        <span>第{{ review.round }}轮</span>
                                    </div>
                                    <!-- 第三行：任务名 -->
                                    <div class="mt-0.5 text-[11px] text-muted-foreground/50 truncate">
                                        {{ review.task_name }}
                                    </div>
                                </button>
                            </div>
                            <div v-else
                                class="flex flex-col items-center justify-center flex-1 py-16 text-muted-foreground/40">
                                <ClipboardCheck class="h-6 w-6 mb-2" />
                                <p class="text-sm">暂无审查记录</p>
                            </div>
                        </div>

                        <!-- 分页 -->
                        <div v-if="pageData.total_pages > 1"
                            class="flex items-center justify-center gap-2 py-2 border-t border-border/30 text-xs text-muted-foreground shrink-0">
                            <Button variant="ghost" size="icon" class="h-7 w-7"
                                :disabled="pageData.page <= 1 || loading" @click="goToPage(pageData.page - 1)">
                                <ArrowLeft class="h-3 w-3" />
                            </Button>
                            <span class="tabular-nums">{{ pageData.page }} / {{ pageData.total_pages }}</span>
                            <Button variant="ghost" size="icon" class="h-7 w-7"
                                :disabled="pageData.page >= pageData.total_pages || loading"
                                @click="goToPage(pageData.page + 1)">
                                <ArrowRight class="h-3 w-3" />
                            </Button>
                        </div>
                    </template>
                </div>

                <!-- 右栏：详情 -->
                <div class="flex-1 min-w-0 overflow-y-auto relative">
                    <!-- 加载中 -->
                    <div v-if="loadingDetail" class="flex items-center justify-center h-full">
                        <Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
                    </div>

                    <!-- 错误 -->
                    <div v-else-if="detailError" class="flex flex-col items-center justify-center h-full">
                        <AlertCircle class="h-5 w-5 text-muted-foreground" />
                        <p class="mt-2 text-sm">{{ detailError }}</p>
                    </div>

                    <!-- 详情内容 -->
                    <div v-else-if="selectedReview" :key="detailKey"
                        class="p-5 space-y-5 max-w-2xl mx-auto animate-slide-up">
                        <!-- 头部 -->
                        <div>
                            <div class="flex items-center gap-2 mb-2">
                                <Badge v-if="selectedReview.result === 'approved'"
                                    class="bg-emerald-100 text-emerald-700 border-emerald-200">
                                    <CheckCircle2 class="h-3 w-3 mr-1" /> 审查通过
                                </Badge>
                                <Badge v-else class="bg-rose-100 text-rose-700 border-rose-200">
                                    <XCircle class="h-3 w-3 mr-1" /> 审查驳回
                                </Badge>
                                <Badge variant="outline" class="text-[10px]">第{{ selectedReview.round }}轮</Badge>
                            </div>
                            <h2 class="text-lg font-semibold">{{ selectedReview.sub_task_name }}</h2>
                            <p class="text-sm text-muted-foreground mt-0.5">{{ selectedReview.task_name }}</p>
                        </div>

                        <Separator />

                        <!-- 评分 -->
                        <div>
                            <div class="text-xs font-medium text-muted-foreground/60 uppercase tracking-wider mb-2">
                                评分
                            </div>
                            <div class="flex items-center gap-3">
                                <span class="text-2xl text-amber-500 tracking-wider">{{
                                    scoreStars(selectedReview.score) }}</span>
                                <span class="text-lg font-bold tabular-nums">{{ selectedReview.score }}/5</span>
                            </div>
                        </div>

                        <!-- 审查意见 -->
                        <div v-if="selectedReview.comment">
                            <div class="text-xs font-medium text-muted-foreground/60 uppercase tracking-wider mb-2">
                                审查意见
                            </div>
                            <div
                                class="rounded-lg border border-border/50 bg-muted/20 p-3 text-sm leading-relaxed whitespace-pre-wrap">
                                {{ selectedReview.comment }}
                            </div>
                        </div>

                        <!-- 问题 -->
                        <div v-if="selectedReview.issues">
                            <div class="text-xs font-medium text-muted-foreground/60 uppercase tracking-wider mb-2">
                                发现问题
                            </div>
                            <div
                                class="rounded-lg border border-rose-200/50 bg-rose-50/30 p-3 text-sm leading-relaxed whitespace-pre-wrap">
                                {{ selectedReview.issues }}
                            </div>
                        </div>

                        <Separator />

                        <!-- 子任务信息 -->
                        <div>
                            <div class="text-xs font-medium text-muted-foreground/60 uppercase tracking-wider mb-2">
                                子任务信息
                            </div>
                            <div class="space-y-2">
                                <div v-if="selectedReview.sub_task_description"
                                    class="rounded-lg border border-border/50 bg-muted/20 p-3">
                                    <div class="text-[11px] text-muted-foreground/60 mb-1">描述</div>
                                    <p class="text-sm">{{ selectedReview.sub_task_description }}</p>
                                </div>
                                <div v-if="selectedReview.sub_task_deliverable"
                                    class="rounded-lg border border-border/50 bg-muted/20 p-3">
                                    <div class="text-[11px] text-muted-foreground/60 mb-1">交付物要求</div>
                                    <p class="text-sm">{{ selectedReview.sub_task_deliverable }}</p>
                                </div>
                                <div v-if="selectedReview.sub_task_acceptance"
                                    class="rounded-lg border border-border/50 bg-muted/20 p-3">
                                    <div class="text-[11px] text-muted-foreground/60 mb-1">验收标准</div>
                                    <p class="text-sm">{{ selectedReview.sub_task_acceptance }}</p>
                                </div>
                            </div>
                        </div>

                        <Separator />

                        <!-- 关联信息 -->
                        <div>
                            <div class="text-xs font-medium text-muted-foreground/60 uppercase tracking-wider mb-2">
                                关联信息
                            </div>
                            <div class="grid grid-cols-2 gap-3">
                                <div class="rounded-lg border border-border/50 bg-muted/20 p-3">
                                    <div class="text-[11px] text-muted-foreground/60">审查 Agent</div>
                                    <div class="mt-1 text-sm font-medium">{{ selectedReview.reviewer_agent_name ||
                                        '—' }}</div>
                                </div>
                                <div class="rounded-lg border border-border/50 bg-muted/20 p-3">
                                    <div class="text-[11px] text-muted-foreground/60">返工指派</div>
                                    <div class="mt-1 text-sm font-medium">{{ selectedReview.rework_agent_name ||
                                        '—' }}</div>
                                </div>
                                <div class="rounded-lg border border-border/50 bg-muted/20 p-3">
                                    <div class="text-[11px] text-muted-foreground/60">审查时间</div>
                                    <div class="mt-1 text-sm font-medium">{{ formatDate(selectedReview.created_at) }}
                                    </div>
                                </div>
                                <div v-if="selectedReview.module_name"
                                    class="rounded-lg border border-border/50 bg-muted/20 p-3">
                                    <div class="text-[11px] text-muted-foreground/60">所属模块</div>
                                    <div class="mt-1 text-sm font-medium">{{ selectedReview.module_name }}</div>
                                </div>
                            </div>
                            <div class="flex gap-4 text-[11px] text-muted-foreground/60 pt-2">
                                <span>审查 ID: {{ selectedReview.id }}</span>
                            </div>
                        </div>
                    </div>

                    <!-- 未选择 -->
                    <div v-if="!loadingDetail && !detailError && !selectedReview"
                        class="flex flex-col items-center justify-center flex-1 h-full text-muted-foreground/40">
                        <ClipboardCheck class="h-8 w-8 mb-3" />
                        <p class="text-sm font-medium text-muted-foreground/60">点击左侧审查记录查看详情</p>
                        <p class="text-xs mt-1">评分、审查意见和子任务信息会在这里展示</p>
                    </div>
                </div>
            </div>
        </div>
    </TooltipProvider>
</template>

<style scoped>
@keyframes slide-up-fade-in {
    from {
        opacity: 0;
        transform: translateY(12px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-slide-up {
    animation: slide-up-fade-in 0.35s ease-out both;
}
</style>
