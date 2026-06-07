/**
 * Справочные карточки птиц для CLIP-поиска (ДЗ2).
 * desc     — английское описание: используется как CLIP text-query.
 * classId  — 0 Альбатрос | 1 Тупик | 2 Пингвин
 */
export const BIRD_CARDS = [
  // ── Альбатрос (classId: 0, id: 1-10) ────────────────────────────────────────
  {
    id: 1, classId: 0,
    name: 'Странствующий альбатрос',
    desc: 'Wandering albatross gliding over Southern Ocean, massive 3.5m wingspan, white plumage with black wingtips',
  },
  {
    id: 2, classId: 0,
    name: 'Чернобровый альбатрос',
    desc: 'Black-browed albatross with yellow-orange bill and distinctive dark eyebrow stripe, soaring over Atlantic',
  },
  {
    id: 3, classId: 0,
    name: 'Тёмноспинный альбатрос',
    desc: 'Black-footed albatross with dark plumage and pale face near Hawaiian islands',
  },
  {
    id: 4, classId: 0,
    name: 'Альбатрос Лайсана',
    desc: 'Laysan albatross with white head and dark back nesting on Pacific atoll',
  },
  {
    id: 5, classId: 0,
    name: 'Королевский альбатрос',
    desc: 'Northern royal albatross landing on cliff edge with large pink-orange bill, New Zealand',
  },
  {
    id: 6, classId: 0,
    name: 'Серый альбатрос',
    desc: 'Grey-headed albatross with grey head and neck, yellow bill with black tip, sub-Antarctic',
  },
  {
    id: 7, classId: 0,
    name: 'Тристанский альбатрос',
    desc: 'Tristan albatross nesting on Gough Island, critically endangered seabird with white body and mottled wings',
  },
  {
    id: 8, classId: 0,
    name: 'Альбатрос в бурю',
    desc: 'Wandering albatross banking effortlessly through violent ocean storm, riding wind gusts without flapping wings',
  },
  {
    id: 9, classId: 0,
    name: 'Птенец альбатроса',
    desc: 'Fluffy white albatross chick sitting on grass nest mound, large grey bill, Falkland Islands',
  },
  {
    id: 10, classId: 0,
    name: 'Альбатрос у корабля',
    desc: 'Albatross gliding behind fishing trawler, white wings spanning over churning ship wake, Southern Ocean',
  },

  // ── Тупик (classId: 1, id: 11-20) ────────────────────────────────────────────
  {
    id: 11, classId: 1,
    name: 'Атлантический тупик',
    desc: 'Atlantic puffin with colorful triangular orange bill standing on rocky cliff, Iceland',
  },
  {
    id: 12, classId: 1,
    name: 'Тупик с уловом',
    desc: 'Atlantic puffin holding row of small silver sand eels in bright orange beak',
  },
  {
    id: 13, classId: 1,
    name: 'Топорок',
    desc: 'Tufted puffin with long golden plumes and massive red bill on Pacific rocky coast',
  },
  {
    id: 14, classId: 1,
    name: 'Ипатка',
    desc: 'Horned puffin standing on basalt rock, black and white plumage with orange-yellow bill base',
  },
  {
    id: 15, classId: 1,
    name: 'Гагарка',
    desc: 'Razorbill auk on sea cliff, closest living relative of puffin, thick blunt black bill',
  },
  {
    id: 16, classId: 1,
    name: 'Тупик в полёте',
    desc: 'Atlantic puffin in fast flight over grey ocean, wings blurred, orange feet trailing',
  },
  {
    id: 17, classId: 1,
    name: 'Тупик в море зимой',
    desc: 'Atlantic puffin floating on open winter ocean, plain dark plumage without colorful summer bill',
  },
  {
    id: 18, classId: 1,
    name: 'Пара тупиков',
    desc: 'Two Atlantic puffins billing and bonding at burrow entrance, affectionate mating behavior, Iceland',
  },
  {
    id: 19, classId: 1,
    name: 'Птенец тупика',
    desc: 'Fluffy grey puffling chick peering from burrow entrance, round head, Skomer Island, Wales',
  },
  {
    id: 20, classId: 1,
    name: 'Тупик у норки',
    desc: 'Atlantic puffin landing at grass burrow entrance with sand eels in beak, Shetland Islands',
  },

  // ── Пингвин (classId: 2, id: 21-30) ─────────────────────────────────────────
  {
    id: 21, classId: 2,
    name: 'Императорский пингвин',
    desc: 'Emperor penguin colony on Antarctic sea ice, tallest and heaviest living penguin species',
  },
  {
    id: 22, classId: 2,
    name: 'Галстучный пингвин',
    desc: 'Gentoo penguin running on sandy beach, recognized by orange beak and white head stripe',
  },
  {
    id: 23, classId: 2,
    name: 'Очковый пингвин',
    desc: 'African penguin on South African rocky shore, black horseshoe marking on white chest',
  },
  {
    id: 24, classId: 2,
    name: 'Малый пингвин',
    desc: 'Little blue penguin, smallest penguin species, walking on Australian beach at dusk',
  },
  {
    id: 25, classId: 2,
    name: 'Пингвин Адели',
    desc: 'Adelie penguin marching across Antarctic ice, distinctive white eye ring on black cap',
  },
  {
    id: 26, classId: 2,
    name: 'Скальный пингвин',
    desc: 'Rockhopper penguin with yellow spiky crest jumping between rocks on sub-Antarctic island',
  },
  {
    id: 27, classId: 2,
    name: 'Пингвин прыгает',
    desc: 'Gentoo penguin porpoising and leaping from sea onto rocky shore, motion blur, Falkland Islands',
  },
  {
    id: 28, classId: 2,
    name: 'Пингвин с птенцом',
    desc: 'Emperor penguin balancing fluffy grey chick on feet, sheltering beneath warm belly, Antarctic ice',
  },
  {
    id: 29, classId: 2,
    name: 'Пингвин под водой',
    desc: 'African penguin swimming underwater with wings as flippers, streamlined torpedo body, blue water',
  },
  {
    id: 30, classId: 2,
    name: 'Пингвин Магеллана',
    desc: 'Magellanic penguin with two distinctive black chest bands, standing on Patagonian coast, Argentina',
  },
]

/** Карточки отфильтрованные по classId */
export function getCardsByClass(classId) {
  return BIRD_CARDS.filter(c => c.classId === classId)
}
