/**
 * @typedef {{ emoji: string, latin: string, weight: string, description: string }} BirdMeta
 */

/** @type {Record<string, BirdMeta>} */
const birdMeta = {
  'пингвин': {
    emoji: '🐧',
    latin: 'Spheniscidae',
    weight: '1,1–45 кг',
    description:
      'Пингвины (Spheniscidae) — семейство нелетающих морских птиц, насчитывающее около 18 видов, ' +
      'распространённых преимущественно в Южном полушарии. Тело пингвинов обтекаемой формы ' +
      'приспособлено для плавания: крылья видоизменены в плавники, а плотное оперение создаёт ' +
      'водонепроницаемый слой. Наиболее крупный представитель семейства — императорский пингвин — ' +
      'достигает роста 120 см и массы до 45 кг.',
  },
  'тупик': {
    emoji: '🐦',
    latin: 'Fratercula arctica',
    weight: '310–650 г',
    description:
      'Тупик атлантический (Fratercula arctica) — морская птица семейства чистиковых, обитающая ' +
      'в Северной Атлантике и Арктике. Отличительная черта вида — крупный, ярко окрашенный клюв ' +
      'оранжево-красного цвета. Тупики — превосходные ныряльщики: они способны погружаться на ' +
      'глубину до 60 м и удерживать в клюве несколько рыб одновременно.',
  },
  'альбатрос': {
    emoji: '🦅',
    latin: 'Diomedeidae',
    weight: '2,5–12 кг',
    description:
      'Альбатросы (Diomedeidae) — крупные морские птицы, известные исключительным размахом крыльев, ' +
      'достигающим у странствующего альбатроса 3,5 м — рекорда среди всех современных птиц. ' +
      'Большую часть жизни они проводят в открытом океане, искусно используя восходящие потоки ' +
      'воздуха для планирования, почти не затрачивая энергии на полёт.',
  },
}

/** @type {BirdMeta} */
const BIRD_META_FALLBACK = {
  emoji: '🐦',
  latin: '',
  weight: 'Нет данных',
  description: 'Описание для данного вида пока недоступно.',
}

/**
 * Looks up bird metadata by class label returned from the backend.
 * Normalises to lowercase before lookup so casing differences are tolerated.
 *
 * @param {string | null | undefined} label
 * @returns {BirdMeta}
 */
export function getBirdMeta(label) {
  if (!label) return BIRD_META_FALLBACK
  return birdMeta[label.trim().toLowerCase()] ?? BIRD_META_FALLBACK
}
