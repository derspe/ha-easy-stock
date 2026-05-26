export interface Strings {
  editor: {
    title_label: string;
    display_currency: string;
    // Card-level label, framed as the *default* since per-asset overrides exist.
    default_display_currency: string;
    default_range: string;
    tile_size: string;
    selected: string;
    drag_hint: string;
    add: string;
    no_sensors: string;
    setup_hint: string;
    // Per-asset currency dropdown: option meaning "no override, use the card default".
    currency_inherit: string;
  };
  card: {
    not_found: string;
  };
}

const translations: Record<string, Strings> = {
  en: {
    editor: {
      title_label: "Title (optional)",
      display_currency: "Display currency",
      default_display_currency: "Default display currency",
      default_range: "Default time range",
      tile_size: "Tile size",
      selected: "Selected",
      drag_hint: "drag to reorder",
      add: "Add",
      no_sensors: "No Easy Stock sensors found.",
      setup_hint: "Set up under Settings → Integrations → Easy Stock.",
      currency_inherit: "Default",
    },
    card: { not_found: "Not found" },
  },
  de: {
    editor: {
      title_label: "Titel (optional)",
      display_currency: "Anzeigewährung",
      default_display_currency: "Standard-Anzeigewährung",
      default_range: "Standard Zeitraum",
      tile_size: "Kachelgröße",
      selected: "Ausgewählt",
      drag_hint: "ziehen zum Sortieren",
      add: "Hinzufügen",
      no_sensors: "Keine Easy Stock Sensoren gefunden.",
      setup_hint: "Integration einrichten unter Einstellungen → Integrationen → Easy Stock.",
      currency_inherit: "Standard",
    },
    card: { not_found: "Nicht gefunden" },
  },
  fr: {
    editor: {
      title_label: "Titre (optionnel)",
      display_currency: "Devise d'affichage",
      default_display_currency: "Devise d'affichage par défaut",
      default_range: "Période par défaut",
      tile_size: "Taille des tuiles",
      selected: "Sélectionnés",
      drag_hint: "glisser pour réorganiser",
      add: "Ajouter",
      no_sensors: "Aucun capteur Easy Stock trouvé.",
      setup_hint: "Configurer sous Paramètres → Intégrations → Easy Stock.",
      currency_inherit: "Par défaut",
    },
    card: { not_found: "Introuvable" },
  },
  nl: {
    editor: {
      title_label: "Titel (optioneel)",
      display_currency: "Weergavevaluta",
      default_display_currency: "Standaard weergavevaluta",
      default_range: "Standaard tijdsbereik",
      tile_size: "Tegelgrootte",
      selected: "Geselecteerd",
      drag_hint: "slepen om te sorteren",
      add: "Toevoegen",
      no_sensors: "Geen Easy Stock-sensoren gevonden.",
      setup_hint: "Instellen via Instellingen → Integraties → Easy Stock.",
      currency_inherit: "Standaard",
    },
    card: { not_found: "Niet gevonden" },
  },
  es: {
    editor: {
      title_label: "Título (opcional)",
      display_currency: "Moneda de visualización",
      default_display_currency: "Moneda de visualización predeterminada",
      default_range: "Rango de tiempo predeterminado",
      tile_size: "Tamaño de ficha",
      selected: "Seleccionados",
      drag_hint: "arrastrar para ordenar",
      add: "Añadir",
      no_sensors: "No se encontraron sensores Easy Stock.",
      setup_hint: "Configurar en Ajustes → Integraciones → Easy Stock.",
      currency_inherit: "Predeterminada",
    },
    card: { not_found: "No encontrado" },
  },
  it: {
    editor: {
      title_label: "Titolo (opzionale)",
      display_currency: "Valuta di visualizzazione",
      default_display_currency: "Valuta di visualizzazione predefinita",
      default_range: "Intervallo predefinito",
      tile_size: "Dimensione tessera",
      selected: "Selezionati",
      drag_hint: "trascina per riordinare",
      add: "Aggiungi",
      no_sensors: "Nessun sensore Easy Stock trovato.",
      setup_hint: "Configurare in Impostazioni → Integrazioni → Easy Stock.",
      currency_inherit: "Predefinita",
    },
    card: { not_found: "Non trovato" },
  },
  pt: {
    editor: {
      title_label: "Título (opcional)",
      display_currency: "Moeda de exibição",
      default_display_currency: "Moeda de exibição padrão",
      default_range: "Intervalo padrão",
      tile_size: "Tamanho do bloco",
      selected: "Selecionados",
      drag_hint: "arrastar para reordenar",
      add: "Adicionar",
      no_sensors: "Nenhum sensor Easy Stock encontrado.",
      setup_hint: "Configurar em Definições → Integrações → Easy Stock.",
      currency_inherit: "Padrão",
    },
    card: { not_found: "Não encontrado" },
  },
  pl: {
    editor: {
      title_label: "Tytuł (opcjonalny)",
      display_currency: "Waluta wyświetlania",
      default_display_currency: "Domyślna waluta wyświetlania",
      default_range: "Domyślny zakres czasu",
      tile_size: "Rozmiar kafelka",
      selected: "Wybrane",
      drag_hint: "przeciągnij, aby zmienić kolejność",
      add: "Dodaj",
      no_sensors: "Nie znaleziono czujników Easy Stock.",
      setup_hint: "Skonfiguruj w Ustawienia → Integracje → Easy Stock.",
      currency_inherit: "Domyślna",
    },
    card: { not_found: "Nie znaleziono" },
  },
  sv: {
    editor: {
      title_label: "Titel (valfritt)",
      display_currency: "Visningsvaluta",
      default_display_currency: "Standardvisningsvaluta",
      default_range: "Standardtidsintervall",
      tile_size: "Kakelstorlek",
      selected: "Valda",
      drag_hint: "dra för att sortera",
      add: "Lägg till",
      no_sensors: "Inga Easy Stock-sensorer hittades.",
      setup_hint: "Konfigurera under Inställningar → Integrationer → Easy Stock.",
      currency_inherit: "Standard",
    },
    card: { not_found: "Hittades inte" },
  },
  da: {
    editor: {
      title_label: "Titel (valgfrit)",
      display_currency: "Visningsvaluta",
      default_display_currency: "Standardvisningsvaluta",
      default_range: "Standard tidsinterval",
      tile_size: "Flisestørrelse",
      selected: "Valgte",
      drag_hint: "træk for at sortere",
      add: "Tilføj",
      no_sensors: "Ingen Easy Stock-sensorer fundet.",
      setup_hint: "Opsæt under Indstillinger → Integrationer → Easy Stock.",
      currency_inherit: "Standard",
    },
    card: { not_found: "Ikke fundet" },
  },
  nb: {
    editor: {
      title_label: "Tittel (valgfritt)",
      display_currency: "Visningsvaluta",
      default_display_currency: "Standard visningsvaluta",
      default_range: "Standard tidsintervall",
      tile_size: "Flisestørrelse",
      selected: "Valgte",
      drag_hint: "dra for å sortere",
      add: "Legg til",
      no_sensors: "Ingen Easy Stock-sensorer funnet.",
      setup_hint: "Konfigurer under Innstillinger → Integrasjoner → Easy Stock.",
      currency_inherit: "Standard",
    },
    card: { not_found: "Ikke funnet" },
  },
  fi: {
    editor: {
      title_label: "Otsikko (valinnainen)",
      display_currency: "Näyttövaluutta",
      default_display_currency: "Oletusnäyttövaluutta",
      default_range: "Oletusjaksovali",
      tile_size: "Ruudun koko",
      selected: "Valitut",
      drag_hint: "vedä järjestääksesi",
      add: "Lisää",
      no_sensors: "Easy Stock -antureita ei löydy.",
      setup_hint: "Määritä kohdassa Asetukset → Integraatiot → Easy Stock.",
      currency_inherit: "Oletus",
    },
    card: { not_found: "Ei löydy" },
  },
  cs: {
    editor: {
      title_label: "Název (volitelný)",
      display_currency: "Zobrazovaná měna",
      default_display_currency: "Výchozí zobrazovaná měna",
      default_range: "Výchozí časový rozsah",
      tile_size: "Velikost dlaždice",
      selected: "Vybrané",
      drag_hint: "přetáhněte pro seřazení",
      add: "Přidat",
      no_sensors: "Nebyly nalezeny žádné senzory Easy Stock.",
      setup_hint: "Nastavte v Nastavení → Integrace → Easy Stock.",
      currency_inherit: "Výchozí",
    },
    card: { not_found: "Nenalezeno" },
  },
  hu: {
    editor: {
      title_label: "Cím (opcionális)",
      display_currency: "Megjelenítési pénznem",
      default_display_currency: "Alapértelmezett megjelenítési pénznem",
      default_range: "Alapértelmezett időtartomány",
      tile_size: "Csempe mérete",
      selected: "Kiválasztottak",
      drag_hint: "húzza a rendezéshez",
      add: "Hozzáadás",
      no_sensors: "Nem találhatók Easy Stock érzékelők.",
      setup_hint: "Állítsa be a Beállítások → Integrációk → Easy Stock menüpontban.",
      currency_inherit: "Alapértelmezett",
    },
    card: { not_found: "Nem található" },
  },
  ru: {
    editor: {
      title_label: "Заголовок (необязательно)",
      display_currency: "Валюта отображения",
      default_display_currency: "Валюта отображения по умолчанию",
      default_range: "Временной диапазон по умолчанию",
      tile_size: "Размер плитки",
      selected: "Выбранные",
      drag_hint: "перетащите для сортировки",
      add: "Добавить",
      no_sensors: "Датчики Easy Stock не найдены.",
      setup_hint: "Настройте в Настройки → Интеграции → Easy Stock.",
      currency_inherit: "По умолчанию",
    },
    card: { not_found: "Не найдено" },
  },
  zh: {
    editor: {
      title_label: "标题（可选）",
      display_currency: "显示货币",
      default_display_currency: "默认显示货币",
      default_range: "默认时间范围",
      tile_size: "磁贴大小",
      selected: "已选择",
      drag_hint: "拖动以排序",
      add: "添加",
      no_sensors: "未找到 Easy Stock 传感器。",
      setup_hint: "在设置 → 集成 → Easy Stock 中进行配置。",
      currency_inherit: "默认",
    },
    card: { not_found: "未找到" },
  },
  ja: {
    editor: {
      title_label: "タイトル（省略可）",
      display_currency: "表示通貨",
      default_display_currency: "デフォルト表示通貨",
      default_range: "デフォルト期間",
      tile_size: "タイルサイズ",
      selected: "選択済み",
      drag_hint: "ドラッグして並び替え",
      add: "追加",
      no_sensors: "Easy Stock センサーが見つかりません。",
      setup_hint: "設定 → インテグレーション → Easy Stock で設定してください。",
      currency_inherit: "デフォルト",
    },
    card: { not_found: "見つかりません" },
  },
  ko: {
    editor: {
      title_label: "제목 (선택사항)",
      display_currency: "표시 통화",
      default_display_currency: "기본 표시 통화",
      default_range: "기본 기간",
      tile_size: "타일 크기",
      selected: "선택됨",
      drag_hint: "드래그하여 정렬",
      add: "추가",
      no_sensors: "Easy Stock 센서를 찾을 수 없습니다.",
      setup_hint: "설정 → 통합 → Easy Stock에서 설정하세요.",
      currency_inherit: "기본값",
    },
    card: { not_found: "찾을 수 없음" },
  },
  tr: {
    editor: {
      title_label: "Başlık (isteğe bağlı)",
      display_currency: "Görüntüleme para birimi",
      default_display_currency: "Varsayılan görüntüleme para birimi",
      default_range: "Varsayılan zaman aralığı",
      tile_size: "Kutucuk boyutu",
      selected: "Seçilenler",
      drag_hint: "sıralamak için sürükle",
      add: "Ekle",
      no_sensors: "Easy Stock sensörü bulunamadı.",
      setup_hint: "Ayarlar → Entegrasyonlar → Easy Stock altında yapılandırın.",
      currency_inherit: "Varsayılan",
    },
    card: { not_found: "Bulunamadı" },
  },
  ar: {
    editor: {
      title_label: "العنوان (اختياري)",
      display_currency: "عملة العرض",
      default_display_currency: "عملة العرض الافتراضية",
      default_range: "النطاق الزمني الافتراضي",
      tile_size: "حجم البلاطة",
      selected: "المحددة",
      drag_hint: "اسحب للترتيب",
      add: "إضافة",
      no_sensors: "لم يتم العثور على أجهزة استشعار Easy Stock.",
      setup_hint: "الإعداد في الإعدادات ← التكاملات ← Easy Stock.",
      currency_inherit: "افتراضي",
    },
    card: { not_found: "غير موجود" },
  },
};

export function t(lang: string): Strings {
  // Normalize: "zh-Hans" → "zh", "pt-BR" → "pt", "nb-NO" → "nb"
  const base = lang.split("-")[0].toLowerCase();
  return translations[base] ?? translations["en"];
}
