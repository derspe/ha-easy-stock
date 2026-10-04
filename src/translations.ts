export interface Strings {
  editor: {
    title_label: string;
    default_range: string;
    tile_size: string;
    selected: string;
    drag_hint: string;
    add: string;
    no_sensors: string;
    setup_hint: string;
  };
  card: {
    not_found: string;
  };
}

const translations: Record<string, Strings> = {
  en: {
    editor: {
      title_label: "Title (optional)",
      default_range: "Default time range",
      tile_size: "Tile size",
      selected: "Selected",
      drag_hint: "drag to reorder",
      add: "Add",
      no_sensors: "No Zwitserleven Fondsen sensors found.",
      setup_hint: "Set up under Settings → Integrations → Zwitserleven Fondsen.",
    },
    card: { not_found: "Not found" },
  },
  de: {
    editor: {
      title_label: "Titel (optional)",
      default_range: "Standard Zeitraum",
      tile_size: "Kachelgröße",
      selected: "Ausgewählt",
      drag_hint: "ziehen zum Sortieren",
      add: "Hinzufügen",
      no_sensors: "Keine Zwitserleven Fondsen Sensoren gefunden.",
      setup_hint: "Integration einrichten unter Einstellungen → Integrationen → Zwitserleven Fondsen.",
    },
    card: { not_found: "Nicht gefunden" },
  },
  fr: {
    editor: {
      title_label: "Titre (optionnel)",
      default_range: "Période par défaut",
      tile_size: "Taille des tuiles",
      selected: "Sélectionnés",
      drag_hint: "glisser pour réorganiser",
      add: "Ajouter",
      no_sensors: "Aucun capteur Zwitserleven Fondsen trouvé.",
      setup_hint: "Configurer sous Paramètres → Intégrations → Zwitserleven Fondsen.",
    },
    card: { not_found: "Introuvable" },
  },
  nl: {
    editor: {
      title_label: "Titel (optioneel)",
      default_range: "Standaard tijdsbereik",
      tile_size: "Tegelgrootte",
      selected: "Geselecteerd",
      drag_hint: "slepen om te sorteren",
      add: "Toevoegen",
      no_sensors: "Geen Zwitserleven Fondsen-sensoren gevonden.",
      setup_hint: "Instellen via Instellingen → Integraties → Zwitserleven Fondsen.",
    },
    card: { not_found: "Niet gevonden" },
  },
  es: {
    editor: {
      title_label: "Título (opcional)",
      default_range: "Rango de tiempo predeterminado",
      tile_size: "Tamaño de ficha",
      selected: "Seleccionados",
      drag_hint: "arrastrar para ordenar",
      add: "Añadir",
      no_sensors: "No se encontraron sensores Zwitserleven Fondsen.",
      setup_hint: "Configurar en Ajustes → Integraciones → Zwitserleven Fondsen.",
    },
    card: { not_found: "No encontrado" },
  },
  it: {
    editor: {
      title_label: "Titolo (opzionale)",
      default_range: "Intervallo predefinito",
      tile_size: "Dimensione tessera",
      selected: "Selezionati",
      drag_hint: "trascina per riordinare",
      add: "Aggiungi",
      no_sensors: "Nessun sensore Zwitserleven Fondsen trovato.",
      setup_hint: "Configurare in Impostazioni → Integrazioni → Zwitserleven Fondsen.",
    },
    card: { not_found: "Non trovato" },
  },
  pt: {
    editor: {
      title_label: "Título (opcional)",
      default_range: "Intervalo padrão",
      tile_size: "Tamanho do bloco",
      selected: "Selecionados",
      drag_hint: "arrastar para reordenar",
      add: "Adicionar",
      no_sensors: "Nenhum sensor Zwitserleven Fondsen encontrado.",
      setup_hint: "Configurar em Definições → Integrações → Zwitserleven Fondsen.",
    },
    card: { not_found: "Não encontrado" },
  },
  pl: {
    editor: {
      title_label: "Tytuł (opcjonalny)",
      default_range: "Domyślny zakres czasu",
      tile_size: "Rozmiar kafelka",
      selected: "Wybrane",
      drag_hint: "przeciągnij, aby zmienić kolejność",
      add: "Dodaj",
      no_sensors: "Nie znaleziono czujników Zwitserleven Fondsen.",
      setup_hint: "Skonfiguruj w Ustawienia → Integracje → Zwitserleven Fondsen.",
    },
    card: { not_found: "Nie znaleziono" },
  },
  sv: {
    editor: {
      title_label: "Titel (valfritt)",
      default_range: "Standardtidsintervall",
      tile_size: "Kakelstorlek",
      selected: "Valda",
      drag_hint: "dra för att sortera",
      add: "Lägg till",
      no_sensors: "Inga Zwitserleven Fondsen-sensorer hittades.",
      setup_hint: "Konfigurera under Inställningar → Integrationer → Zwitserleven Fondsen.",
    },
    card: { not_found: "Hittades inte" },
  },
  da: {
    editor: {
      title_label: "Titel (valgfrit)",
      default_range: "Standard tidsinterval",
      tile_size: "Flisestørrelse",
      selected: "Valgte",
      drag_hint: "træk for at sortere",
      add: "Tilføj",
      no_sensors: "Ingen Zwitserleven Fondsen-sensorer fundet.",
      setup_hint: "Opsæt under Indstillinger → Integrationer → Zwitserleven Fondsen.",
    },
    card: { not_found: "Ikke fundet" },
  },
  nb: {
    editor: {
      title_label: "Tittel (valgfritt)",
      default_range: "Standard tidsintervall",
      tile_size: "Flisestørrelse",
      selected: "Valgte",
      drag_hint: "dra for å sortere",
      add: "Legg til",
      no_sensors: "Ingen Zwitserleven Fondsen-sensorer funnet.",
      setup_hint: "Konfigurer under Innstillinger → Integrasjoner → Zwitserleven Fondsen.",
    },
    card: { not_found: "Ikke funnet" },
  },
  fi: {
    editor: {
      title_label: "Otsikko (valinnainen)",
      default_range: "Oletusjaksovali",
      tile_size: "Ruudun koko",
      selected: "Valitut",
      drag_hint: "vedä järjestääksesi",
      add: "Lisää",
      no_sensors: "Zwitserleven Fondsen -antureita ei löydy.",
      setup_hint: "Määritä kohdassa Asetukset → Integraatiot → Zwitserleven Fondsen.",
    },
    card: { not_found: "Ei löydy" },
  },
  cs: {
    editor: {
      title_label: "Název (volitelný)",
      default_range: "Výchozí časový rozsah",
      tile_size: "Velikost dlaždice",
      selected: "Vybrané",
      drag_hint: "přetáhněte pro seřazení",
      add: "Přidat",
      no_sensors: "Nebyly nalezeny žádné senzory Zwitserleven Fondsen.",
      setup_hint: "Nastavte v Nastavení → Integrace → Zwitserleven Fondsen.",
    },
    card: { not_found: "Nenalezeno" },
  },
  hu: {
    editor: {
      title_label: "Cím (opcionális)",
      default_range: "Alapértelmezett időtartomány",
      tile_size: "Csempe mérete",
      selected: "Kiválasztottak",
      drag_hint: "húzza a rendezéshez",
      add: "Hozzáadás",
      no_sensors: "Nem találhatók Zwitserleven Fondsen érzékelők.",
      setup_hint: "Állítsa be a Beállítások → Integrációk → Zwitserleven Fondsen menüpontban.",
    },
    card: { not_found: "Nem található" },
  },
  ru: {
    editor: {
      title_label: "Заголовок (необязательно)",
      default_range: "Временной диапазон по умолчанию",
      tile_size: "Размер плитки",
      selected: "Выбранные",
      drag_hint: "перетащите для сортировки",
      add: "Добавить",
      no_sensors: "Датчики Zwitserleven Fondsen не найдены.",
      setup_hint: "Настройте в Настройки → Интеграции → Zwitserleven Fondsen.",
    },
    card: { not_found: "Не найдено" },
  },
  zh: {
    editor: {
      title_label: "标题（可选）",
      default_range: "默认时间范围",
      tile_size: "磁贴大小",
      selected: "已选择",
      drag_hint: "拖动以排序",
      add: "添加",
      no_sensors: "未找到 Zwitserleven Fondsen 传感器。",
      setup_hint: "在设置 → 集成 → Zwitserleven Fondsen 中进行配置。",
    },
    card: { not_found: "未找到" },
  },
  ja: {
    editor: {
      title_label: "タイトル（省略可）",
      default_range: "デフォルト期間",
      tile_size: "タイルサイズ",
      selected: "選択済み",
      drag_hint: "ドラッグして並び替え",
      add: "追加",
      no_sensors: "Zwitserleven Fondsen センサーが見つかりません。",
      setup_hint: "設定 → インテグレーション → Zwitserleven Fondsen で設定してください。",
    },
    card: { not_found: "見つかりません" },
  },
  ko: {
    editor: {
      title_label: "제목 (선택사항)",
      default_range: "기본 기간",
      tile_size: "타일 크기",
      selected: "선택됨",
      drag_hint: "드래그하여 정렬",
      add: "추가",
      no_sensors: "Zwitserleven Fondsen 센서를 찾을 수 없습니다.",
      setup_hint: "설정 → 통합 → Zwitserleven Fondsen에서 설정하세요.",
    },
    card: { not_found: "찾을 수 없음" },
  },
  tr: {
    editor: {
      title_label: "Başlık (isteğe bağlı)",
      default_range: "Varsayılan zaman aralığı",
      tile_size: "Kutucuk boyutu",
      selected: "Seçilenler",
      drag_hint: "sıralamak için sürükle",
      add: "Ekle",
      no_sensors: "Zwitserleven Fondsen sensörü bulunamadı.",
      setup_hint: "Ayarlar → Entegrasyonlar → Zwitserleven Fondsen altında yapılandırın.",
    },
    card: { not_found: "Bulunamadı" },
  },
  ar: {
    editor: {
      title_label: "العنوان (اختياري)",
      default_range: "النطاق الزمني الافتراضي",
      tile_size: "حجم البلاطة",
      selected: "المحددة",
      drag_hint: "اسحب للترتيب",
      add: "إضافة",
      no_sensors: "لم يتم العثور على أجهزة استشعار Zwitserleven Fondsen.",
      setup_hint: "الإعداد في الإعدادات ← التكاملات ← Zwitserleven Fondsen.",
    },
    card: { not_found: "غير موجود" },
  },
};

export function t(lang: string): Strings {
  // Normalize: "zh-Hans" → "zh", "pt-BR" → "pt", "nb-NO" → "nb"
  const base = lang.split("-")[0].toLowerCase();
  return translations[base] ?? translations["en"];
}
