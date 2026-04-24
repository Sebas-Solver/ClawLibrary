export type UiLocale = 'en' | 'zh' | 'es';

export const RESOURCE_LABELS: Record<string, Record<UiLocale, string>> = {
  document: { en: 'Documents Archive', zh: '文档归档', es: 'Archivo de Documentos' },
  images: { en: 'Image Atelier', zh: '图像工坊', es: 'Taller de Imágenes' },
  memory: { en: 'Memory Vault', zh: '记忆库', es: 'Bóveda de Memoria' },
  skills: { en: 'Skill Forge', zh: '技能锻炉', es: 'Fragua de Skills' },
  gateway: { en: 'Interface Gateway', zh: '接口网关', es: 'Puerta de Enlace' },
  log: { en: 'Log Deck', zh: '日志台', es: 'Panel de Logs' },
  mcp: { en: 'Code Lab', zh: '代码实验室', es: 'Code Lab' },
  schedule: { en: 'Scheduler Deck', zh: '调度台', es: 'Panel del Programador' },
  alarm: { en: 'Alert Deck', zh: '报警台', es: 'Panel de Alertas' },
  agent: { en: 'Run Dock', zh: '运行监控', es: 'Muelle de Ejecución' },
  task_queues: { en: 'Queue Hub', zh: '队列中枢', es: 'Centro de Colas' },
  break_room: { en: 'Breakroom', zh: '休息室', es: 'Sala de Descanso' }
};

export const UI_TEXT = {
  title: { en: 'ClawLibrary', zh: '龙虾图书馆', es: 'ClawLibrary' },
  recentActivity: { en: 'Recent Activity', zh: '最近活动', es: 'Actividad Reciente' },
  noActivity: { en: 'No recent activity yet.', zh: '暂时还没有最近活动。', es: 'Aún no hay actividad reciente.' },
  archiveLive: { en: 'ARCHIVE LIVE', zh: '实时归档', es: 'ARCHIVO EN VIVO' },
  quickRooms: { en: 'Quick room routing', zh: '快速房间路由', es: 'Acceso rápido a salas' },
  statsAssets: { en: 'assets', zh: '资产', es: 'recursos' },
  statsLive: { en: 'live', zh: '在线', es: 'en vivo' },
  statsEvents: { en: 'events 24h', zh: '24h 事件', es: 'eventos 24h' },
  waiting: { en: 'waiting', zh: '等待中', es: 'esperando' },
  hideInfo: { en: 'Hide Info', zh: '隐藏信息', es: 'Ocultar Info' },
  showInfo: { en: 'Show Info', zh: '显示信息', es: 'Mostrar Info' },
  shortcuts: { en: 'Shortcuts', zh: '快捷键', es: 'Atajos' },
  search: { en: 'Search', zh: '搜索', es: 'Buscar' },
  copyContext: { en: 'Copy Context', zh: '复制上下文', es: 'Copiar Contexto' },
  close: { en: 'Close', zh: '关闭', es: 'Cerrar' },
  grid: { en: 'Grid', zh: '网格', es: 'Cuadrícula' },
  list: { en: 'List', zh: '列表', es: 'Lista' },
  allKinds: { en: 'All Kinds', zh: '全部分类', es: 'Todos' },
  recommended: { en: 'Recommended', zh: '推荐', es: 'Recomendados' },
  newest: { en: 'Newest', zh: '最新', es: 'Más recientes' },
  oldest: { en: 'Oldest', zh: '最早', es: 'Más antiguos' },
  largest: { en: 'Largest', zh: '最大', es: 'Más grandes' },
  smallest: { en: 'Smallest', zh: '最小', es: 'Más pequeños' },
  theme: { en: 'Theme', zh: '主题', es: 'Tema' },
  debug: { en: 'Debug', zh: '调试', es: 'Depuración' },
  clawSkin: { en: 'Claw', zh: '爪形', es: 'Skin' },
  preview: { en: 'Preview', zh: '预览', es: 'Vista previa' },
  loadingPreview: { en: 'Loading preview…', zh: '预览加载中…', es: 'Cargando vista previa…' },
  open: { en: 'Open', zh: '打开', es: 'Abrir' },
  openFolder: { en: 'Open Folder', zh: '打开目录', es: 'Abrir Carpeta' },
  copyPath: { en: 'Copy Path', zh: '复制路径', es: 'Copiar Ruta' },
  copyExcerpt: { en: 'Copy Excerpt', zh: '复制摘要', es: 'Copiar Extracto' },
  openSource: { en: 'Open Source', zh: '打开来源', es: 'Abrir Origen' },
  copySource: { en: 'Copy Source', zh: '复制来源', es: 'Copiar Origen' },
  openTopItem: { en: 'Open Top Item', zh: '打开首项', es: 'Abrir Primer Elemento' },
  copyDetail: { en: 'Copy Detail', zh: '复制详情', es: 'Copiar Detalle' },
  topItem: { en: 'Top Item', zh: '首项', es: 'Primer Elemento' },
  recentEvents: { en: 'Recent Events', zh: '最近事件', es: 'Eventos Recientes' },
  status: { en: 'Status', zh: '状态', es: 'Estado' },
  source: { en: 'Source', zh: '来源', es: 'Origen' },
  signal: { en: 'Signal', zh: '信号', es: 'Señal' },
  focus: { en: 'Focus', zh: '焦点', es: 'Foco' },
  pointer: { en: 'Pointer', zh: '指针', es: 'Puntero' },
  client: { en: 'Client', zh: '屏幕', es: 'Cliente' },
  scene: { en: 'Scene', zh: '场景', es: 'Escena' },
  lastClick: { en: 'Last Click', zh: '上次点击', es: 'Último Clic' },
  clickClient: { en: 'Click Client', zh: '点击屏幕', es: 'Clic Cliente' },
  stageInside: { en: 'Inside Stage', zh: '在场景内', es: 'Dentro del Escenario' },
  stageOutside: { en: 'Outside Stage', zh: '场景外', es: 'Fuera del Escenario' },
  active: { en: 'Active', zh: '活跃', es: 'Activo' },
  idle: { en: 'Idle', zh: '空闲', es: 'Inactivo' },
  alert: { en: 'Alert', zh: '告警', es: 'Alerta' },
  offline: { en: 'Offline', zh: '离线', es: 'Desconectado' }
} as const;

export function resourceLabel(id: string, locale: UiLocale): string {
  return RESOURCE_LABELS[id]?.[locale] ?? id;
}

export function uiText<K extends keyof typeof UI_TEXT>(key: K, locale: UiLocale): string {
  return UI_TEXT[key][locale];
}
