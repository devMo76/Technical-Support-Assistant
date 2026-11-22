# Ten starter QA questions

Documentation: v3.5.1, commit 35b0439195bbdb87a6d519152e6782abe0720c3b.

These are development examples, created from documented situations. They are not real staff submissions, a held-out evaluation, or proof of working software. Nine are answerable; one requires live information. English, Arabic, mixed terms, and an exact error are covered.

## Q01 (EN)

**Question:** Can I assign more than one tag to a document?

**Expected answer:** Yes. A document can have multiple tags, so it can belong to several groups.

**Evidence:**

[documents/usage.md, lines 30–52](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/usage.md#L30-L52)

```text
with a single tag, however, a single document can also have multiple
  tags. This is not possible with folders. The reason folders are not
  implemented in paperless is simply that tags are much more versatile
  than folders.
- A _document type_ is used to demarcate the type of a document such
  as letter, bank statement, invoice, contract, etc. It is used to
  identify what a document is about.
- The document _storage path_ is the location where the document files
  are stored. See [Storage Paths](advanced_usage.md#storage-paths) for
  more information.
- The _date added_ of a document is the date the document was scanned
  into paperless. You cannot and should not change this date.
- The _date created_ of a document is the date the document was
  initially issued. This can be the date you bought a product, the
  date you signed a contract, or the date a letter was sent to you.
- The _archive serial number_ (short: ASN) of a document is the
  identifier of the document in your physical document binders. See
  [recommended workflow](#usage-recommended-workflow) below.
- The _content_ of a document is the text that was OCR'ed from the
  document. This text is fed into the search engine and is used for
  matching tags, correspondents and document types.
- Paperless-ngx also supports _custom fields_ which can be used to
  store additional metadata about a document.
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q02 (AR)

**Question:** أنشأت مستخدمًا جديدًا، لكنه لا يستطيع استخدام أجزاء من النظام. ما الذي أراجعه؟

**Expected answer:** راجع الصلاحيات المباشرة وصلاحيات المجموعات. المستخدم الجديد لا يحصل افتراضيًا على صلاحيات، باستثناء ما يرثه من مجموعاته.

**Evidence:**

[documents/usage.md, lines 409–409](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/usage.md#L409-L409)

```text
By default, new users are not granted any permissions, except those inherited from any group(s) of which they are a member.
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q03 (AR)

**Question:** هل تغيير صلاحيات الوسم يغيّر صلاحيات المستندات التي تحمل هذا الوسم؟

**Expected answer:** لا. صلاحيات الوسم تخص الوسم نفسه، ولا تغيّر صلاحيات المستندات المرتبطة به.

**Evidence:**

[documents/usage.md, lines 385–386](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/usage.md#L385-L386)

```text
Object-level permissions only apply to the object itself. In other words, setting permissions
    for a Tag will _not_ affect the permissions of documents that have the Tag.
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q04 (EN)

**Question:** What must I configure to enable password reset emails?

**Expected answer:** Configure an SMTP backend, including PAPERLESS_EMAIL_HOST. Also configure PAPERLESS_URL or its corresponding settings.

**Evidence:**

[documents/usage.md, lines 465–467](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/usage.md#L465-L467)

```text
In order to enable the password reset feature you will need to setup an SMTP backend, see
[`PAPERLESS_EMAIL_HOST`](configuration.md#PAPERLESS_EMAIL_HOST). You should also set
[`PAPERLESS_URL`](configuration.md#PAPERLESS_URL) and / or its corresponding configuration settings.
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q05 (EN)

**Question:** What must be installed before following the Docker Compose installation instructions?

**Expected answer:** Docker and Docker Compose must be installed.

**Evidence:**

[documents/setup.md, lines 47–48](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/setup.md#L47-L48)

```text
- Docker and Docker Compose must be [installed](https://docs.docker.com/engine/install/){:target="\_blank"}.
- macOS users will need [GNU sed](https://formulae.brew.sh/formula/gnu-sed) with support for running as `sed` as well as [wget](https://formulae.brew.sh/formula/wget).
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q06 (MIXED)

**Question:** ما الفرق بين PAPERLESS_OCR_LANGUAGE وPAPERLESS_OCR_LANGUAGES؟

**Expected answer:** الأول يحدد لغة أو لغات OCR المستخدمة فعليًا. الثاني يثبت حزم لغات إضافية في نشر Docker المدعوم. تثبيت اللغة وحده لا يفعّل استخدامها؛ يجب أيضًا تحديد لغة OCR. خيار تثبيت اللغات غير مخصص للحاويات rootless.

**Evidence:**

[documents/configuration.md, lines 2003–2009](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/configuration.md#L2003-L2009)

```text
: Additional OCR languages to install. By default, paperless comes
with English, German, Italian, Spanish and French. If your language
is not in this list, install additional languages with this
configuration option. You will need to [find the right LangCodes](https://tesseract-ocr.github.io/tessdoc/Data-Files-in-different-versions.html)
but note that [tesseract-ocr-\* package names](https://packages.debian.org/bullseye/graphics/)
do not always correspond with the language codes e.g. "chi_tra" should be
specified as "chi-tra".
```

[documents/configuration.md, lines 2017–2018](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/configuration.md#L2017-L2018)

```text
To actually use these languages, also set the default OCR language
    of paperless:
```

[documents/configuration.md, lines 2028–2028](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/configuration.md#L2028-L2028)

```text
This option must not be used in rootless containers.
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q07 (EN)

**Question:** I put files in the consumption folder, but no documents are added. What should I check first?

**Expected answer:** Check the watched folder or Docker folder mapping, the message broker, and the task processor. Inspect logs and failed tasks in the admin interface. These are checks, not a confirmed diagnosis.

**Evidence:**

[documents/troubleshooting.md, lines 7–11](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/troubleshooting.md#L7-L11)

```text
- Ensure that the directory you're putting your documents in is the
  folder paperless is watching. With docker, this setting is performed
  in the `docker-compose.yml` file. Without Docker, look at the
  `CONSUMPTION_DIR` setting. Don't adjust this setting if you're
  using docker.
```

[documents/troubleshooting.md, lines 13–15](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/troubleshooting.md#L13-L15)

```text
- Ensure that the broker is up and running. Paperless does its task
  processing asynchronously, and for documents to arrive at the task
  processor, it needs the broker to run.
```

[documents/troubleshooting.md, lines 17–18](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/troubleshooting.md#L17-L18)

```text
- Ensure that the task processor is running. Docker does this
  automatically. Manually invoke the task processor by executing
```

[documents/troubleshooting.md, lines 26–27](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/troubleshooting.md#L26-L27)

```text
- Go to the admin interface, and check if there are failed tasks. If
  so, the tasks will contain an error message.
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q08 (EN)

**Question:** Processing document.pdf fails with [Errno 13] Permission denied in the consumption directory. What should I check?

**Expected answer:** Check that Paperless can delete files there and that the host directory is readable and writable. For Docker, verify USERMAP_UID and USERMAP_GID match the intended host user/group when they differ from the default 1000.

**Evidence:**

[documents/troubleshooting.md, lines 144–147](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/troubleshooting.md#L144-L147)

```text
This happens when paperless does not have permission to delete files
inside the consumption directory. Ensure that `USERMAP_UID` and
`USERMAP_GID` are set to the user id and group id you use on the host
operating system, if these are different from `1000`. See [Docker setup](setup.md#docker).
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q09 (EN)

**Question:** Does the document exporter include document metadata as well as files?

**Expected answer:** Yes. Its target includes documents, thumbnails, and manifest.json. The manifest contains database metadata such as correspondents and tags.

**Evidence:**

[documents/administration.md, lines 309–311](https://github.com/paperless-ngx/paperless-ngx/blob/35b0439195bbdb87a6d519152e6782abe0720c3b/docs/administration.md#L309-L311)

```text
`target` is a folder to which the data gets written. This includes
documents, thumbnails and a `manifest.json` file. The manifest contains
all metadata from the database (correspondents, tags, etc).
```

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.

## Q10 (EN)

**Question:** How much free disk space is on my Paperless server right now?

**Expected answer:** Explain that static documentation cannot reveal live server disk usage. Ask the user for current disk-usage information; do not invent a number or claim to have inspected the server.

**Evidence:**

No static source can establish current private server state.

**Pass later:** answer preserves the expected facts and cites supporting evidence; for Q10, it states the limitation and asks for current information.
