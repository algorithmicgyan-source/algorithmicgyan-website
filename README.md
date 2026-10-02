# Algorithmic Gyan Website — Deploy Guide (Hindi)

Ye tumhare YouTube channel **Algorithmic Gyan** ki official website hai.
Isme tum khud **News, Facts, Current Affairs aur Motivational Stories** add kar sakte ho — koi coding nahi karni padegi.

## Tumhe kya chahiye (sab free)
- GitHub account → [github.com](https://github.com)
- Netlify account → [app.netlify.com](https://app.netlify.com) (GitHub se login ho jayega)

## Step 1 — GitHub par repo banao
1. [github.com](https://github.com) par login karo
2. Upar **+** → **New repository**
3. Naam rakho: `algorithmic-gyan-website`
4. **Public** select karo → **Create repository**

## Step 2 — Website files upload karo
1. Naye repo page par **"uploading an existing file"** par click karo
2. Is zip ko kholo, andar ki **saari files aur folders** drag-drop karo
3. Neeche **Commit changes** dabao

## Step 3 — Admin me apna repo naam likho (zaroori!)
1. Repo me `admin/config.yml` file kholo → pencil ✏️ (Edit) par click karo
2. Ye line dhoondo:
   `repo: APNA-USERNAME/algorithmic-gyan-website`
3. `APNA-USERNAME` ki jagah **apna GitHub username** likho. Example:
   `repo: algorithmicgyan/algorithmic-gyan-website`
4. **Commit changes** dabao

## Step 4 — Netlify par site LIVE karo
1. [app.netlify.com](https://app.netlify.com) → **GitHub se login** karo
2. **Add new site** → **Import an existing project** → **GitHub**
3. Apna `algorithmic-gyan-website` repo select karo → **Deploy site** dabao
4. 1–2 minute me site live! Tumhe link milega jaise: `tumhara-naam.netlify.app`

## Step 5 — Admin login setup (posts add karne ke liye)
1. Netlify me apni site kholo → **Site settings** → **Identity** → **Enable Identity**
2. **Services** → **Git Gateway** → **Enable Git Gateway**
3. Upar **Identity** tab → **Invite users** → apna email likho
4. Email me aaye link se **password set** karo
5. Ab `tumhari-site.netlify.app/admin` kholo → login karo
6. **Posts** → **＋ Add** → Title, Category (News/Facts/Current Affairs/Motivational), Date, Description, YouTube link → **Publish**!
7. Site apne aap update ho jayegi — kuch nahi karna padega.

## Step 6 — Google Search me lao
1. [search.google.com/search-console](https://search.google.com/search-console) par jao → apni site add karo
2. Left me **Sitemaps** → `sitemap.xml` likh kar **Submit** karo
3. Google kuch din me site ko padh lega (indexing). Uske baad **"Algorithmic Gyan"** search karne par site dikhne lagegi.
4. Note: pehle number par aana content aur time par depend karta hai — par apne unique naam se dikhna shuru ho jayegi.

## Apni photo lagana (Owner section)
1. Apni ek achhi photo ko **`owner.jpg`** naam do
2. GitHub repo me `assets/` folder kholo → **Add file → Upload files** → `owner.jpg` upload karo
3. Agar pehle se `owner.jpg` hai to wahi replace ho jayegi
4. Site par Home page me tumhari photo + naam dikhne lagega
5. Naam badalne ke liye: `index.html` me `__APNA_NAAM__` ki jagah apna naam likho

## Apna domain lagana (optional, baad me)
- Domain kharido (jaise `algorithmicgyan.com`, ~₹900/saal)
- Netlify → apni site → **Domain settings** → **Add custom domain**

---
Kisi bhi step me atko to mujhe batao — main guide kar dunga! 🚀
