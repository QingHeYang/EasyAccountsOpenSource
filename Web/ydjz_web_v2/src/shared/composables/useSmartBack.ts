import { useRouter } from 'vue-router'
import { useRouteHistoryStore } from '@shared/stores/routeHistory'

/**
 * 智能返回 composable
 *
 * 使用方法：
 * const { smartBack } = useSmartBack()
 *
 * // 返回上一页，如果没有历史则跳转到 /flow
 * smartBack('/flow')
 *
 * // 返回上一页，如果没有历史则跳转到默认页 /board
 * smartBack()
 */
export function useSmartBack() {
  const router = useRouter()
  const routeHistory = useRouteHistoryStore()

  /**
   * 智能返回
   * @param fallback 没有历史时的回退路径，默认 /board
   */
  function smartBack(fallback: string = '/board') {
    const previous = routeHistory.getPrevious(fallback)
    router.replace(previous)
  }

  /**
   * 返回到指定页面，同时清理历史中该页面之后的记录
   * @param path 目标路径
   */
  function backTo(path: string) {
    router.replace(path)
  }

  /**
   * 提交完成后跳列表，自动清理 add/edit 路径栈，避免点返回后又回到刚提交过的表单页。
   *
   * 用法：
   *   replaceAfterSubmit('/setting/type')
   *   → 清掉历史中 /setting/type/add* 和 /setting/type/edit* 路径，再 router.replace('/setting/type')
   *
   * 也可以指定自定义前缀：
   *   replaceAfterSubmit('/setting/type', ['/setting/type/add', '/setting/type/edit', '/setting/type/archive'])
   *
   * @param listPath 列表页路径（也是跳转目标）
   * @param prefixes 要从历史栈中清理的路径前缀。不传时默认清掉 `${listPath}/add` 和 `${listPath}/edit`
   */
  function replaceAfterSubmit(listPath: string, prefixes?: string[]) {
    const list = prefixes ?? [`${listPath}/add`, `${listPath}/edit`]
    routeHistory.removeWhere((p) => list.some((prefix) => p.startsWith(prefix)))
    router.replace(listPath)
  }

  return {
    smartBack,
    backTo,
    replaceAfterSubmit,
  }
}
