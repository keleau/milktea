// common/js/date.js —— 补回教程缺失的 Date 原型扩展，不改变任何调用方
function pad(n) { return n < 10 ? '0' + n : '' + n }
Date.prototype.VP_FORMAT = function (fmt) {
  const map = {
    'YYYY': this.getFullYear(),
    'MM': pad(this.getMonth() + 1),
    'dd': pad(this.getDate()),
    'hh': pad(this.getHours()),
    'mm': pad(this.getMinutes()),
    'ss': pad(this.getSeconds())
  }
  return fmt.replace(/YYYY|MM|dd|hh|mm|ss/g, k => map[k])
}