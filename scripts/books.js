// ============================================================================
//  BOOK DATA  —  one flat, chronological list (oldest first, newest last).
//
//  Each book carries a `tags` array naming every category it belongs to.
//  To recategorize a book, edit its tag(s) in place — nothing needs to move.
//    tags: "recently-completed" | "currently-reading" | "hexaseptim-tbr" | "all-time-greats"
//  A book may hold several tags and will then appear in each matching row
//  (e.g. a favorite you've read is both "recently-completed" and "all-time-greats").
//
//  `year`  optional — the year a book was read (used only for reference).
//  `rank`  optional — favorites-only; controls the order of the all-time-greats
//          row (1 = shown first). Reorder your favorites by editing these.
//
//  Storage is oldest->newest so new books can simply be appended to the end.
//  The render engine below flips "recently-completed", "currently-reading" and
//  "hexaseptim-tbr" to newest-first for display, so whatever you added most
//  recently leads the row and older entries trail off the end. Only
//  "all-time-greats" ignores position and orders by `rank`.
//  To bump an existing book to the front of a row, move its object to the end
//  of this array — position in the file *is* the display order.
// ============================================================================
const myBooks = [
    {
        title: "The Art of Engineering",
        author: "Richard W. Hamming",
        cover: "the-art-of-engineering-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2020
    },
    {
        title: "Tribe",
        author: "Sebastian Junger",
        cover: "tribe-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2020
    },
    {
        title: "Into the Wild",
        author: "Jon Krakauer",
        cover: "into-the-wild-cover.jpg",
        summary: "The story of Christopher McCandless and his journey into the Alaskan wilderness.",
        tags: ["recently-completed", "all-time-greats"],
        notes: "SPOILER: Chris dies. But I'll be damned that didn't stop me from wanting to adventure into the woods (around the world) and see what happened. If this book clicks with you, I'd also read The Wild Truth by his sister Carine McCandless to get the full story.",
        year: 2020,
        rank: 4
    },
    {
        title: "Marie Kondo's Spark Joy",
        author: "Marie Kondo",
        cover: "marie-kondos-spark-joy-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2021
    },
    {
        title: "Lights Out: A Cyberattack, a Nation Unprepared, Surviving the Aftermath",
        author: "Ted Koppel",
        cover: "lights-out-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2021
    },
    {
        title: "We the Living",
        author: "Ayn Rand",
        cover: "we-the-living-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2021
    },
    {
        title: "Zero to One",
        author: "Peter Thiel",
        cover: "zero-to-one-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2021
    },
    {
        title: "People Skills for Engineers",
        author: "",
        cover: "people-skills-for-engineers-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2021
    },
    {
        title: "The Fountainhead",
        author: "Ayn Rand",
        cover: "the-fountainhead-cover.jpg",
        summary: "A philosophical novel by Ayn Rand about individualism.",
        tags: ["recently-completed", "all-time-greats"],
        notes: "\"Integrity is the ability to stand by an idea. That presupposes the ability to think. Thinking is something one doesn’t borrow or pawn.\" ",
        year: 2022,
        rank: 6
    },
    {
        title: "How to Win Friends and Influence People",
        author: "Dale Carnegie",
        cover: "how-to-win-friends-and-influence-people-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2022
    },
    {
        title: "Man's Search for Meaning",
        author: "Viktor E. Frankl",
        cover: "mans-search-for-meaning-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2022
    },
    {
        title: "$100M Offers",
        author: "Alex Hormozi",
        cover: "100m-offers-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2022
    },
    {
        title: "EQ Applied",
        author: "Justin Bariso",
        cover: "eq-applied-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "27b/6",
        author: "David Thorne",
        cover: "27b-6-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "A Short History of Nearly Everything",
        author: "Bill Bryson",
        cover: "a-short-history-of-nearly-everything-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Feel-Good Productivity",
        author: "Ali Abdaal",
        cover: "feel-good-productivity-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "What We Owe the Future",
        author: "William MacAskill",
        cover: "what-we-owe-the-future-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Engineering in Plain Sight",
        author: "Grady Hillhouse",
        cover: "engineering-in-plain-sight-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Miss Minimalist",
        author: "Francine Jay",
        cover: "miss-minimalist-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "The Impact Identity",
        author: "",
        cover: "the-impact-identity-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Master Your Emotions",
        author: "Thibaut Meurisse",
        cover: "master-your-emotions-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "12 Rules for Life: An Antidote to Chaos",
        author: "Jordan B. Peterson",
        cover: "12-rules-for-life-an-antidote-to-chaos-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Digital Minimalism",
        author: "Cal Newport",
        cover: "digital-minimalism-cover.jpg",
        summary: "A minimalist approach to digital life and productivity.",
        tags: ["recently-completed", "all-time-greats"],
        notes: "This is the book that put me on the right path to escape from content and technology addiction. Have slowly deleted all of my social media and tried various ways of reducing technology dependency in my life because of it, and will continue to do so throughout my life. I think this book was so good because it perfectly validated the mindeset I had going into it so I'm hesitant to recommend to everyone, but if you stress about using your phone and computer all day, and scrolling on social media apps all the time, you'll probably like it.",
        year: 2023,
        rank: 3
    },
    {
        title: "The Oz Principle: Getting Results Through Individual and Organizational Accountability",
        author: "Roger Connors, Tom Smith, and Craig Hickman",
        cover: "the-oz-principle-getting-results-through-individual-and-organizational-accountability-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "The 7 Habits of Highly Effective People",
        author: "Stephen R. Covey",
        cover: "the-7-habits-of-highly-effective-people-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "PARA Method",
        author: "Tiago Forte",
        cover: "para-method-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "The Art of Setting Smart Goals",
        author: "",
        cover: "the-art-of-setting-smart-goals-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Finite and Infinite Games",
        author: "James P. Carse",
        cover: "finite-and-infinite-games-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "As a Man Thinketh",
        author: "James Allen",
        cover: "as-a-man-thinketh-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Deep Work: Rules for Focused Success in a Distracted World",
        author: "Cal Newport",
        cover: "deep-work-rules-for-focused-success-in-a-distracted-world-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Atomic Habits",
        author: "James Clear",
        cover: "atomic-habits-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "The Pathless Path",
        author: "Paul Millerd",
        cover: "the-pathless-path-cover.jpg",
        summary: "A new view on how to progress through life.",
        tags: ["recently-completed", "all-time-greats"],
        notes: "I like this book a lot because it empowered me to question the \"default\" where others see no choice. I've spent the last few years actively auditing my life against his principles:\n\n**Deleted social media** to reclaim my attention.\n**Going car-free** to reject the machinery-dependent default.\n**Traveled the world** because the barriers are largely an illusion.\n\nNow, I am moving across the world to build a life entirely on my own terms, trusting that an uncertain future is not a problem to be solved.",
        year: 2023,
        rank: 7
    },
    {
        title: "Building a Second Brain",
        author: "Tiago Forte",
        cover: "building-a-second-brain-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Beyond Wealth: The Road Map to a Rich Life",
        author: "Alexander Green",
        cover: "beyond-wealth-the-road-map-to-a-rich-life-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Checklist",
        author: "",
        cover: "checklist-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Rapt",
        author: "Winifred Gallagher",
        cover: "rapt-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "The Power of Now",
        author: "Eckhart Tolle",
        cover: "the-power-of-now-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Models",
        author: "Mark Manson",
        cover: "models-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Poems for the Lost Because Lost Too",
        author: "",
        cover: "poems-for-the-lost-because-lost-too-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Three Alarms",
        author: "",
        cover: "three-alarms-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "How to Develop a Personal Mission Statement",
        author: "Stephen R. Covey",
        cover: "how-to-develop-a-personal-mission-statement-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Project Hail Mary",
        author: "Andy Weir",
        cover: "project-hail-mary-cover.jpg",
        summary: "A gripping sci-fi novel by Andy Weir, creator of The Martian.",
        tags: ["recently-completed", "all-time-greats"],
        notes: "One of my if not my favorite book of all time. Have listened to and read the book (and watched the movie, not as good). Would highly recommend this to pretty much anyone looking for a good sci-fi read!",
        year: 2023,
        rank: 1
    },
    {
        title: "How to Avoid a Climate Disaster",
        author: "Bill Gates",
        cover: "how-to-avoid-a-climate-disaster-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2023
    },
    {
        title: "Children of Time",
        author: "Adrian Tchaikovsky",
        cover: "children-of-time-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Friends of the City",
        author: "",
        cover: "friends-of-the-city-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Designing Your Life",
        author: "Bill Burnett and Dave Evans",
        cover: "designing-your-life-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Ego Is the Enemy",
        author: "Ryan Holiday",
        cover: "ego-is-the-enemy-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Grit",
        author: "Angela Duckworth",
        cover: "grit-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Slow Productivity",
        author: "Cal Newport",
        cover: "slow-productivity-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Sustainable Hedonism",
        author: "Orsolya Lelkes",
        cover: "sustainable-hedonism-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Art of Frugal Hedonism",
        author: "Annie Raser-Rowland and Adam Grubb",
        cover: "the-art-of-frugal-hedonism-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Obstacle Is the Way",
        author: "Ryan Holiday",
        cover: "the-obstacle-is-the-way-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Unofficial ALDI Cookbook",
        author: "Jeanette Hurt",
        cover: "the-unofficial-aldi-cookbook-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Scandinavia",
        author: "",
        cover: "scandinavia-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Martian",
        author: "Andy Weir",
        cover: "the-martian-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Can't Hurt Me",
        author: "David Goggins",
        cover: "cant-hurt-me-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Life, the Universe and Everything",
        author: "Douglas Adams",
        cover: "life-the-universe-and-everything-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Restaurant at the End of the Universe",
        author: "Douglas Adams",
        cover: "the-restaurant-at-the-end-of-the-universe-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Discipline Equals Freedom",
        author: "Jocko Willink",
        cover: "discipline-equals-freedom-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Stillness Is the Key",
        author: "Ryan Holiday",
        cover: "stillness-is-the-key-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Hitchhiker's Guide to the Galaxy",
        author: "Douglas Adams",
        cover: "the-hitchhikers-guide-to-the-galaxy-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The R-Value",
        author: "",
        cover: "the-r-value-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Type R",
        author: "Ama Marston and Stephanie Marston",
        cover: "type-r-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Positive Disintegration",
        author: "Kazimierz Dabrowski",
        cover: "positive-disintegration-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "So Long, and Thanks for All the Fish",
        author: "Douglas Adams",
        cover: "so-long-and-thanks-for-all-the-fish-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Mostly Harmless",
        author: "Douglas Adams",
        cover: "mostly-harmless-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Dirk Gently's Holistic Detective Agency",
        author: "Douglas Adams",
        cover: "dirk-gentlys-holistic-detective-agency-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Long Dark Tea-Time of the Soul",
        author: "Douglas Adams",
        cover: "the-long-dark-tea-time-of-the-soul-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "And Another Thing...",
        author: "Eoin Colfer",
        cover: "and-another-thing-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Subtle Art of Not Giving a F*ck",
        author: "Mark Manson",
        cover: "the-subtle-art-of-not-giving-a-f-ck-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Salmon of Doubt",
        author: "Douglas Adams",
        cover: "the-salmon-of-doubt-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "A World Without Email",
        author: "Cal Newport",
        cover: "a-world-without-email-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "80,000 Hours: Find a Fulfilling Career That Does Good",
        author: "Benjamin Todd",
        cover: "80-000-hours-find-a-fulfilling-career-that-does-good-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "How to Win at Chess",
        author: "Levy Rozman",
        cover: "how-to-win-at-chess-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "The Wild Truth",
        author: "Carine McCandless",
        cover: "the-wild-truth-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2024
    },
    {
        title: "Doing Good Better",
        author: "William MacAskill",
        cover: "doing-good-better-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "How to Hold a Cockroach",
        author: "Matthew Maxwell",
        cover: "how-to-hold-a-cockroach-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Four Thousand Weeks",
        author: "Oliver Burkeman",
        cover: "four-thousand-weeks-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Anti-Tech Revolution: Why and How",
        author: "Theodore J. Kaczynski",
        cover: "anti-tech-revolution-why-and-how-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "The Book Censor's Library",
        author: "Bothayna Al-Essa",
        cover: "the-book-censors-library-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Time Reborn",
        author: "Lee Smolin",
        cover: "time-reborn-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Deaf Again",
        author: "Mark Drolsbaugh",
        cover: "deaf-again-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Lonely Planet Eastern Europe",
        author: "Lonely Planet",
        cover: "lonely-planet-eastern-europe-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Hooked",
        author: "Nir Eyal",
        cover: "hooked-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Credence",
        author: "Penelope Douglas",
        cover: "credence-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Animal Farm",
        author: "George Orwell",
        cover: "animal-farm-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Piranesi",
        author: "Susanna Clarke",
        cover: "piranesi-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Fahrenheit 451",
        author: "Ray Bradbury",
        cover: "fahrenheit-451-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Baltic: The Future of Europe",
        author: "Oliver Moody",
        cover: "baltic-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Abundance",
        author: "Ezra Klein and Derek Thompson",
        cover: "abundance-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "If Cats Disappeared from the World",
        author: "Genki Kawamura",
        cover: "if-cats-disappeared-from-the-world-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "SPQR",
        author: "Mary Beard",
        cover: "spqr-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2025
    },
    {
        title: "Atlas Shrugged",
        author: "Ayn Rand",
        cover: "atlas-shrugged-cover.jpg",
        summary: "A seminal novel of the Objectivist philosophy.",
        tags: ["recently-completed"],
        notes: "A mentor recommended this to me five years ago alongside The Fountainhead. At the time, Rand’s defense of the individual perfectly mirrored my worldview. Reading it now, I find myself reflecting less on the text itself and more on how much I have evolved in the years since.\n\nWhile the book has merit, its Objectivist undertones serve as a dangerous moral cover in today’s political climate. There is a profound irony in modern \"Randians\" supporting an administration defined by fraud, institutional abuse, and the pseudo-nationalization of industries for personal gain. This shift toward state-sponsored favoritism is a clear departure from the free market—it is, in fact, the exact brand of \"looting\" Rand warned against.",
        year: 2025
    },
    {
        title: "The Devil's Financial Dictionary",
        author: "Jason Zweig",
        cover: "the-devils-financial-dictionary-cover.jpg",
        summary: "A satirical look at financial terms and concepts.",
        tags: ["recently-completed"],
        notes: "'SELF-SERVING BIAS, n. The human tendency to attribute success to one’s own actions but to blame failure on other people or uncontrollable external factors. The old saying “Success has many fathers, while failure is an orphan” has been rewritten by corporate executives and money managers as “Failure has many fathers, but success has only one: Me. \n\nWhen forming expectations of the future, investors should make sure their picture of the past hasn’t been distorted. History books are written by the winners, but history is produced by winners and losers alike.'",
        year: 2025
    },
    {
        title: "How to Not Die Alone",
        author: "Logan Ury",
        cover: "how-to-not-die-alone-cover.jpg",
        summary: "The surprising science that will help you find your match.",
        tags: ["recently-completed"],
        notes: "I doubt many men or uninterested women are looking this in-depth at my website. If you're single make your move beautiful ;)",
        year: 2025
    },
    {
        title: "Superintelligence",
        author: "Nick Bostrom",
        cover: "superintelligence-cover.jpg",
        summary: "Paths, Dangers, Strategies by Nick Bostrom.",
        tags: ["recently-completed"],
        notes: "This book walks through many different possibilities, and makes you think that maybe the world doesn't really need humans.",
        year: 2025
    },
    {
        title: "A New Earth",
        author: "Eckhart Tolle",
        cover: "a-new-earth-cover.jpg",
        summary: "Awakening to Your Life's Purpose.",
        tags: ["recently-completed"],
        notes: "I'm not really a fan of Eckhart Tolle's writing. I read the Power of Now summer 2023 and bought this at the same time - both books I only read half, got bored, and returned to after forgetting how uninterested I was. I really need to learn to quit books more often.",
        year: 2026
    },
    {
        title: "The Contrarian",
        author: "Max Chafkin",
        cover: "the-contrarian-cover.jpg",
        summary: "A biography of Peter Thiel and the pursuit of power in Silicon Valley.",
        tags: ["recently-completed"],
        notes: "This makes me want to be a baddie. I don't know what that word means. In all seriousness,it was a bit motivating with the idea that someone could gain that much power over others, that could be me ya know? But like, a decent human also.",
        year: 2026
    },
    {
        title: "Walden",
        author: "Henry David Thoreau",
        cover: "walden-cover.jpg",
        summary: "A reflection upon simple living in natural surroundings.",
        tags: ["recently-completed"],
        notes: "One of the worst books I've ever committed to reading all the way through. If you want the good parts, read the first and last chapter, everything else is just like the random thoughts that go through your head, but from someone 170 years ago.",
        year: 2026
    },
    {
        title: "Maybe You Should Talk to Someone",
        author: "Lori Gottlieb",
        cover: "maybe-you-should-talk-to-someone-cover.jpg",
        summary: "A therapist's memoir detailing her clinical practice and her own journey as a patient.",
        tags: ["recently-completed"],
        notes: "I deleted my notes for this on accident and I'm not going to rewrite them for you. Nobody will see this anyway. A decent book if it seems up your alley.",
        year: 2026
    },
    {
        title: "The Peter Principle",
        author: "Laurence J. Peter and Raymond Hull",
        cover: "the-peter-principle-cover.jpg",
        summary: "An exploration of how organizational hierarchies promote employees to their level of incompetence.",
        tags: ["recently-completed"],
        notes: "Same your time and read something else. If you really want to read it, get an AI summary instead.",
        year: 2026
    },
    {
        title: "Careless People",
        author: "Sarah Wynn-Williams",
        cover: "careless-people-cover.jpg",
        summary: "A A cautionary tale of power, greed, and lost idealism.",
        tags: ["recently-completed"],
        notes: "Why have morals when you can have money instead?",
        year: 2026
    },
    {
        title: "Amusing Ourselves to Death",
        author: "Neil Postman",
        cover: "amusing-ourselves-to-death-cover.jpg",
        summary: "Public discource in the age of show business.",
        tags: ["recently-completed"],
        notes: "",
        year: 2026
    },
    {
        title: "The Stranger",
        author: "Albert Camus",
        cover: "the-stranger-cover.jpg",
        summary: "A classic existentialist novel set in Algiers.",
        tags: ["recently-completed"],
        notes: "",
        year: 2026
    },
    {
        title: "The Plague",
        author: "Albert Camus",
        cover: "the-plague-cover.jpg",
        summary: "",
        tags: ["recently-completed"],
        notes: "",
        year: 2026
    },
    {
        title: "PMBOK Guide",
        author: "Project Management Institute",
        cover: "pmbok-guide-cover.jpg",
        summary: "The essential reference for project management professionals.",
        tags: ["currently-reading"],
        notes: ""
    },
    {
        title: "Computer Architecture",
        author: "Hennessy & Patterson",
        cover: "computer-architecture-cover.jpg",
        summary: "A quantitative approach to computer architecture and design.",
        tags: ["currently-reading"],
        notes: ""
    },
    {
        title: "Why We Sleep",
        author: "Matthew Walker",
        cover: "why-we-sleep-cover.jpg",
        summary: "Unlocking the power of sleep and dreams.",
        tags: ["hexaseptim-tbr"],
        notes: ""
    },
    {
        title: "Hyperion",
        author: "Dan Simmons",
        cover: "hyperion-cover.jpg",
        summary: "A Hugo Award-winning science fiction epic.",
        tags: ["hexaseptim-tbr"],
        notes: ""
    },
    {
        title: "Friendship, Robots, and Social Media",
        author: "Alexis Elder",
        cover: "friendship-robots-and-social-media-cover.jpg",
        summary: "False friends and second selves.",
        tags: ["hexaseptim-tbr"],
        notes: ""
    },
    {
        title: "Caste",
        author: "Isabel Wilkerson",
        cover: "caste-cover.jpg",
        summary: "The Origins of Our Discontents by Isabel Wilkerson.",
        tags: ["currently-reading"],
        notes: ""
    },
    {
        title: "Meditations",
        author: "Marcus Aurelius",
        cover: "meditations-cover.jpg",
        summary: "Stoic philosophy and personal writings of a Roman emperor.",
        tags: ["hexaseptim-tbr"],
        notes: ""
    },
    {
        title: "Catch-22",
        author: "Joseph Heller",
        cover: "catch-22-cover.jpg",
        summary: "A satirical novel about the absurdity of war.",
        tags: ["hexaseptim-tbr"],
        notes: ""
    },
    {
        title: "The Ultimate Hitchhiker's Guide to the Galaxy",
        author: "Douglas Adams",
        cover: "hitchhikers-guide-to-the-galaxy-cover.jpg",
        summary: "A comedic sci-fi series by Douglas Adams.",
        tags: ["all-time-greats"],
        notes: "I'm gonna cheat and say this is also my favorite sci-fi books (series) of all time. It was a joy to breeze through. Very educational on the necessity and many uses for a travel towel.",
        rank: 2
    },
    {
        title: "Rendezvous with Rama",
        author: "Arthur C. Clarke",
        cover: "rendezvous-with-rama-cover.jpg",
        summary: "A classic hard science fiction novel about a mysterious alien starship.",
        tags: ["all-time-greats"],
        notes: "I listened to the audiobook and can't remember the details, but remember enjoying it. My short term memory looking out for me so I can read the book next time and be just as amazed as the first time through.",
        rank: 5
    },
    {
        title: "The Art of Doing Science and Engineering",
        author: "Richard W. Hamming",
        cover: "doing-science-and-engineering-cover.jpg",
        summary: "Philosophical thoughts on science and engineering from Richard Hamming.",
        tags: ["all-time-greats"],
        notes: "This is one of the first books, if not the first book, that got me back to reading in my adult life. It was a slow start, but there are plenty of books yet to be read.",
        rank: 8
    },
    {
        title: "Wool",
        author: "Hugh Howey",
        cover: "wool-cover.jpg",
        summary: "",
        tags: ["hexaseptim-tbr"],
        notes: ""
    },
    {
        title: "Save the Cat! Writes a Novel",
        author: "Jessica Brody",
        cover: "save-the-cat-writes-a-novel-cover.jpg",
        summary: "",
        tags: ["hexaseptim-tbr"],
        notes: ""
    },
    {
        title: "Siddhartha: An Indian Tale",
        author: "Hermann Hesse",
        cover: "siddhartha-an-indian-tale-cover.jpg",
        summary: "",
        tags: ["currently-reading"],
        notes: ""
    },
];


// ============================================================================
//  RENDER ENGINE  --  one horizontal coverflow carousel per category.
//  The focused cover sits in front; two neighbours on each side recede,
//  shrink, blur and fade before disappearing. Arrows, clicks, swipe and the
//  keyboard all move the focus. Categories keep their column order, stacked
//  top-to-bottom, because the engine fills the existing <div id> containers.
// ============================================================================

// `sort` decides the left-to-right order inside a row.
// (a, b) => b.index - a.index  ==  reverse of storage order  ==  newest-added first,
// since new books are always appended to the end of myBooks.
const CATEGORIES = [
    { id: "recently-completed", sort: (a, b) => b.index - a.index },              // newest read first
    { id: "currently-reading",  sort: (a, b) => b.index - a.index },              // newest added first
    { id: "hexaseptim-tbr",     sort: (a, b) => b.index - a.index },              // newest added first
    { id: "all-time-greats",    sort: (a, b) => (a.book.rank ?? 999) - (b.book.rank ?? 999) },
];

// ============================================================================
//  DEEP LINKING  —  /books#the-glass-hotel focuses that book and opens it.
//
//  Slugs come from the title, so a link stays valid as long as the title does.
//  Renaming a book changes its link; the cover filename is unaffected.
// ============================================================================

function slugifyTitle(title) {
    return String(title)
        .normalize("NFKD")
        .replace(/[\u0300-\u036f]/g, "")     // strip accents
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, "")         // drop punctuation
        .trim()
        .replace(/[\s_-]+/g, "-")
        .replace(/^-+|-+$/g, "");
}

// index -> slug, with -2, -3 suffixes if two books ever share a title
const bookSlugs = (() => {
    const used = new Set();
    return myBooks.map(book => {
        const base = slugifyTitle(book.title) || "book";
        let slug = base, n = 2;
        while (used.has(slug)) slug = `${base}-${n++}`;
        used.add(slug);
        return slug;
    });
})();

const slugToIndex = new Map(bookSlugs.map((slug, i) => [slug, i]));

// bookIndex -> { categoryId: focusFunction }, filled in by buildCarousel
const focusRegistry = new Map();

// A book can sit in several rows. Favorites win, then recently completed.
const FOCUS_PRIORITY = ["all-time-greats", "recently-completed",
                        "currently-reading", "hexaseptim-tbr"];

function focusBook(bookIndex) {
    const rows = focusRegistry.get(bookIndex);
    if (!rows) return false;
    for (const categoryId of FOCUS_PRIORITY) {
        if (rows[categoryId]) { rows[categoryId](); return true; }
    }
    return false;
}

function bookCard(book, index) {
    const authorLine = book.author ? `<p>by ${book.author}</p>` : "";
    const summary    = book.summary ? `<div class="summary">${book.summary}</div>` : "";
    return `
        <div class="book" data-index="${index}">
            <div class="book-cover">
                <img data-src="images/bookCovers/${book.cover}" alt="${book.title}" loading="lazy"
                     onerror="this.onerror=null; this.src='images/bookCovers/question-mark.jpg';" />
                ${summary}
            </div>
            <div class="book-info">
                <h3>${book.title}</h3>
                ${authorLine}
            </div>
        </div>
    `;
}

function buildCarousel(column, entries, categoryId) {
    const carousel = document.createElement("div");
    carousel.className = "carousel";
    carousel.tabIndex = 0;                         // focusable, so arrow keys work
    carousel.innerHTML = `
        <button class="arrow left" aria-label="Previous book" type="button">&#8249;</button>
        <div class="stage"></div>
        <button class="arrow right" aria-label="Next book" type="button">&#8250;</button>
    `;
    const stage    = carousel.querySelector(".stage");
    const leftBtn  = carousel.querySelector(".arrow.left");
    const rightBtn = carousel.querySelector(".arrow.right");
    stage.innerHTML = entries.map(e => bookCard(e.book, e.index)).join("");
    const cards = Array.from(stage.children);
    const n = cards.length;
    const LOAD_AHEAD = 3;   // load the focused cover + this many on each side
    let focus = 0;

    function update() {
        cards.forEach((card, i) => {
            const off = i - focus;
            let pos;
            if      (off ===  0) pos = "pos-0";
            else if (off === -1) pos = "pos-l1";
            else if (off ===  1) pos = "pos-r1";
            else if (off === -2) pos = "pos-l2";
            else if (off ===  2) pos = "pos-r2";
            else                 pos = off < 0 ? "pos-hidden-l" : "pos-hidden-r";
            card.className = "book " + pos;
            card.setAttribute("aria-hidden", pos.startsWith("pos-hidden") ? "true" : "false");

            // lazy-load covers only within a few steps of the focused book
            if (Math.abs(off) <= LOAD_AHEAD) {
                const img = card.querySelector("img");
                if (img && !img.dataset.loaded) {
                    img.src = img.dataset.src;
                    img.dataset.loaded = "1";
                }
            }
        });
        leftBtn.classList.toggle("disabled", focus === 0);
        rightBtn.classList.toggle("disabled", focus === n - 1);
    }

    function go(delta) {
        focus = Math.max(0, Math.min(n - 1, focus + delta));
        update();
    }

    leftBtn.addEventListener("click", () => go(-1));
    rightBtn.addEventListener("click", () => go(1));

    // click a side cover to bring it forward; click the focused cover to open it
    cards.forEach((card, i) => {
        card.addEventListener("click", () => {
            if (i === focus) openModal(parseInt(card.dataset.index, 10));
            else { focus = i; update(); }
        });
    });

    // arrow keys when the row is focused
    carousel.addEventListener("keydown", (e) => {
        if (e.key === "ArrowLeft")  { go(-1); e.preventDefault(); }
        if (e.key === "ArrowRight") { go( 1); e.preventDefault(); }
    });

    // touch swipe
    let startX = null;
    stage.addEventListener("touchstart", (e) => { startX = e.touches[0].clientX; }, { passive: true });
    stage.addEventListener("touchend", (e) => {
        if (startX === null) return;
        const dx = e.changedTouches[0].clientX - startX;
        if (Math.abs(dx) > 40) go(dx < 0 ? 1 : -1);
        startX = null;
    });

    // Register a way to bring each book to the front of THIS row, so a link
    // like /books#the-glass-hotel can focus it later. A book with several tags
    // registers once per row it appears in; FOCUS_PRIORITY picks between them.
    entries.forEach((e, i) => {
        if (!focusRegistry.has(e.index)) focusRegistry.set(e.index, {});
        focusRegistry.get(e.index)[categoryId] = () => {
            focus = i;
            update();
            carousel.scrollIntoView({ behavior: "smooth", block: "center" });
        };
    });

    column.appendChild(carousel);
    update();
}

CATEGORIES.forEach(cfg => {
    const column = document.getElementById(cfg.id);
    if (!column) return;
    const entries = myBooks
        .map((book, index) => ({ book, index }))
        .filter(e => e.book.tags.includes(cfg.id));
    if (cfg.sort) entries.sort(cfg.sort);
    if (entries.length === 0) { column.style.display = "none"; return; }
    buildCarousel(column, entries, cfg.id);
});


// --- MODAL POP-UP LOGIC ---
const modal = document.getElementById("bookModal");
const closeModalBtn = document.querySelector(".close-modal");

function openModal(bookIndex, updateHash = true) {
    const selectedBook = myBooks[bookIndex];
    document.getElementById("modalCover").src = `images/bookCovers/${selectedBook.cover}`;
    document.getElementById("modalTitle").innerText = selectedBook.title;
    document.getElementById("modalAuthor").innerText = selectedBook.author ? `by ${selectedBook.author}` : "";
    document.getElementById("modalSummary").innerText = selectedBook.summary || "";

    if (selectedBook.notes && selectedBook.notes.trim() !== "") {
        document.getElementById("modalNotes").innerText = selectedBook.notes;
    } else {
        document.getElementById("modalNotes").innerText = "I haven't written any notes for this book yet!";
    }
    modal.style.display = "block";

    // Put the slug in the address bar so the URL can just be copied.
    // replaceState rather than pushState: opening books shouldn't stack up
    // history entries the back button has to walk through.
    if (updateHash) {
        history.replaceState(null, "", "#" + bookSlugs[bookIndex]);
    }
}

function closeModal() {
    modal.style.display = "none";
    if (location.hash) {
        history.replaceState(null, "", location.pathname + location.search);
    }
}

closeModalBtn.onclick = closeModal;
window.onclick = function(event) { if (event.target == modal) closeModal(); };
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && modal.style.display === "block") closeModal();
});


// --- DEEP LINK ENTRY POINT ---
// Runs last, once every carousel exists and the modal element is bound.
function openFromHash() {
    const slug = decodeURIComponent(location.hash.replace(/^#/, ""));
    if (!slug) return;
    const bookIndex = slugToIndex.get(slug);
    if (bookIndex === undefined) return;   // unknown slug: leave the page as-is
    focusBook(bookIndex);
    openModal(bookIndex, false);           // hash is already correct
}

openFromHash();
window.addEventListener("hashchange", openFromHash);
