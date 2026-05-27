/**
 * Справочные карточки птиц для CLIP-поиска (ДЗ2).
 * desc              — английское описание: используется как CLIP text-query.
 * defaultSimilarity — базовый % схожести с классом (показывается если CLIP недоступен).
 * classId           — 0 Альбатрос | 1 Тупик | 2 Пингвин
 */
export const BIRD_CARDS = [
  // ── Альбатрос (classId: 0) ────────────────────────────────────────────────
  {
    id: 1, classId: 0, defaultSimilarity: 94,
    name: 'Странствующий альбатрос',
    desc: 'Wandering albatross gliding over Southern Ocean, massive 3.5m wingspan, white plumage with black wingtips',
  },
  {
    id: 2, classId: 0, defaultSimilarity: 87,
    name: 'Чернобровый альбатрос',
    desc: 'Black-browed albatross with yellow-orange bill and distinctive dark eyebrow stripe, soaring over Atlantic',
  },
  {
    id: 3, classId: 0, defaultSimilarity: 81,
    name: 'Тёмноспинный альбатрос',
    desc: 'Black-footed albatross with dark plumage and pale face near Hawaiian islands',
  },
  {
    id: 4, classId: 0, defaultSimilarity: 78,
    name: 'Альбатрос Лайсана',
    desc: 'Laysan albatross with white head and dark back nesting on Pacific atoll',
  },
  {
    id: 5, classId: 0, defaultSimilarity: 84,
    name: 'Королевский альбатрос',
    desc: 'Northern royal albatross landing on cliff edge with large pink-orange bill, New Zealand',
  },
  {
    id: 6, classId: 0, defaultSimilarity: 75,
    name: 'Серый альбатрос',
    desc: 'Grey-headed albatross with grey head and neck, yellow bill with black tip, sub-Antarctic',
  },

  // ── Тупик (classId: 1) ────────────────────────────────────────────────────
  {
    id: 7, classId: 1, defaultSimilarity: 96,
    name: 'Атлантический тупик',
    desc: 'Atlantic puffin with colorful triangular orange bill standing on rocky cliff, Iceland',
  },
  {
    id: 8, classId: 1, defaultSimilarity: 91,
    name: 'Тупик с уловом',
    desc: 'Atlantic puffin holding row of small silver sand eels in bright orange beak',
  },
  {
    id: 9, classId: 1, defaultSimilarity: 83,
    name: 'Топорок',
    desc: 'Tufted puffin with long golden plumes and massive red bill on Pacific rocky coast',
  },
  {
    id: 10, classId: 1, defaultSimilarity: 79,
    name: 'Ипатка',
    desc: 'Horned puffin standing on basalt rock, black and white plumage with orange-yellow bill base',
  },
  {
    id: 11, classId: 1, defaultSimilarity: 71,
    name: 'Гагарка',
    desc: 'Razorbill auk on sea cliff, closest living relative of puffin, thick blunt black bill',
  },
  {
    id: 12, classId: 1, defaultSimilarity: 88,
    name: 'Тупик в полёте',
    desc: 'Atlantic puffin in fast flight over grey ocean, wings blurred, orange feet trailing',
  },

  // ── Пингвин (classId: 2) ──────────────────────────────────────────────────
  {
    id: 13, classId: 2, defaultSimilarity: 95,
    name: 'Императорский пингвин',
    desc: 'Emperor penguin colony on Antarctic sea ice, tallest and heaviest living penguin species',
  },
  {
    id: 14, classId: 2, defaultSimilarity: 89,
    name: 'Галстучный пингвин',
    desc: 'Gentoo penguin running on sandy beach, recognized by orange beak and white head stripe',
  },
  {
    id: 15, classId: 2, defaultSimilarity: 84,
    name: 'Очковый пингвин',
    desc: 'African penguin on South African rocky shore, black horseshoe marking on white chest',
  },
  {
    id: 16, classId: 2, defaultSimilarity: 77,
    name: 'Малый пингвин',
    desc: 'Little blue penguin, smallest penguin species, walking on Australian beach at dusk',
  },
  {
    id: 17, classId: 2, defaultSimilarity: 86,
    name: 'Пингвин Адели',
    desc: 'Adelie penguin marching across Antarctic ice, distinctive white eye ring on black cap',
  },
  {
    id: 18, classId: 2, defaultSimilarity: 81,
    name: 'Скальный пингвин',
    desc: 'Rockhopper penguin with yellow spiky crest jumping between rocks on sub-Antarctic island',
  },
]

/** Карточки отфильтрованные по classId */
export function getCardsByClass(classId) {
  return BIRD_CARDS.filter(c => c.classId === classId)
}
