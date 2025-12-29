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

  return {
    smartBack,
    backTo,
  }
}
