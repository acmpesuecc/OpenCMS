# OpenCMS

> A minimal headless CMS for blog publishing, designed to integrate with hugo, zola, etc SSGs.

> Content is in **git**. CMS edits files, commits changes, serves content and assets.

*This project is part of ACMPESUECC - AIEP'26.*

**Mentees**:
- Kalyani Puranik
- Manav Dewangan
- Prarthana Vadeesha

**Mentors**:
- Mebin J Thattil
- Sabique Islam

---
## MVP features

### Content

* Markdown / MDX editor
* Frontmatter
* Tags, categories
* Live preview

### Assets

* Paste image to upload
* Store in bucket
* Return URL
* Image resize + format convert

### Git

* Connect GitHub
* Select repo + branch
* Read files
* Commit changes

### API

* Fetch raw markdown
* Fetch rendered HTML
* Fetch metadata
* Trigger build via webhook
* POST assets / blogs in md format to the system *[can be V2]*

### Admin

* Single workspace
* Owner + editor roles


### Flexibility *[can be V2]*
* Work with Hugo and other such SSGs 
* Connect to custom domain name
* Bulk export blogs to md, assets to zip file
* SEO optimization hints
* Version controlling and edit history


---

## Tech stack

### Backend

* Python
* GitHub App [for repo access + webhooks]
* Webhooks
* CF Workers

### Frontend

* Flask / FastAPI / Django
* Markdown editor
* Preview renderer (like reddit posts drafting)

### Storage

* Object storage for images 
* CDN in front
* CF R2

### Database

* [Convex](https://www.convex.dev/) or Turso
* Only metadata
  (posts list, tags, repo config, users)

or

* create a bin/posts/[slug] in the repo, for every post with metadata 

### Auth

* GitHub OAuth only


---

## Resources

Would reccomend mentees to take a look at existing CMS such as:
- [decapcms](https://decapcms.org)
- [payloadcms](https://payloadcms.com)
- [marblecms](https://marblecms.com)

Building blocks for this project - SSG and Storage:
- [Anna Docs](https://anna-docs.netlify.app/posts/building-anna)
- [Hugo Docs](https://gohugo.io/documentation)
- [Cloudflare R2](https://developers.cloudflare.com/r2)

Some articles on other folks that have built a CMS before:
- [Building a custom headless CMS](https://medium.com/@vidzhel/building-custom-headless-cms-that-powers-blogging-platform-d6d33515f109)
- [Building a CMS in a day](https://medium.com/@ddamato/how-i-built-a-cms-in-a-day-759b8171926a)



---

## Timeline

### Week 0
* Read up on things
* Ice breakers
* Get familar with the tech stack

### Week 1

* Data model
* GitHub App
* Repo read/write working

### Week 2

* Markdown editor
* Preview renderer

### Week 3

* Asset upload
* Paste handling
* Object storage + CDN

### Week 4

* Admin UI
* Role checks

### Week 5

* Content APIs
* Webhooks
* Rate limits

### Week 6

* Bug fixing
* Performance checks
* Docs
* Deploy

---

## Future plans

* AI assisted writing tools
* Realtime editing for multiple people working on same content
* Plugins
* Custom domains
* Video processing
* Multi-workspaces


---
