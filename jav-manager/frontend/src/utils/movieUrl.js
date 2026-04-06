/**
 * 影片外部链接工具
 */

const JAVBUS_PRIMARY = 'https://javbus.com'
const JAVDB_PRIMARY = 'https://javdb.com'

/**
 * 获取 JavBus 影片页面 URL
 * @param {string} code 影片番号（如 ABC-123）
 */
export function getJavBusUrl(code) {
  return `${JAVBUS_PRIMARY}/${code}`
}

/**
 * 获取 JavDB 影片页面 URL
 * @param {string} code 影片番号
 * @param {string} javdbId 可选的 JavDB ID（更精确）
 */
export function getJavDbUrl(code, javdbId) {
  if (javdbId) {
    return `${JAVDB_PRIMARY}/v/${javdbId}`
  }
  return `${JAVDB_PRIMARY}/search?q=${encodeURIComponent(code)}&f=all`
}
