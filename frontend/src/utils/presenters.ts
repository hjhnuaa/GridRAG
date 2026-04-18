import dayjs from "dayjs";

export function formatDateTime(value?: string | null): string {
  if (!value) {
    return "暂无";
  }
  return dayjs(value).format("YYYY-MM-DD HH:mm");
}

export function formatDay(value?: string | null): string {
  if (!value) {
    return "暂无";
  }
  return dayjs(value).format("YYYY-MM-DD");
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }
  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function categoryLabel(value: string): string {
  const map: Record<string, string> = {
    COMPLAINT: "投诉受理",
    HAZARD: "安全隐患",
    DISPUTE: "矛盾纠纷",
    VISIT: "走访服务",
    OTHER: "其他事项"
  };
  return map[value] ?? value;
}

export function statusLabel(value: string): string {
  const map: Record<string, string> = {
    PENDING: "待处理",
    IN_PROGRESS: "处理中",
    RESOLVED: "已解决",
    CLOSED: "已关闭"
  };
  return map[value] ?? value;
}

export function statusColor(value: string): string {
  const map: Record<string, string> = {
    PENDING: "gold",
    IN_PROGRESS: "processing",
    RESOLVED: "success",
    CLOSED: "default"
  };
  return map[value] ?? "default";
}

export function docTypeLabel(value: string): string {
  const map: Record<string, string> = {
    policy: "政策文件",
    manual: "工作手册",
    ticket: "历史工单",
    case: "典型案例"
  };
  return map[value] ?? value;
}

