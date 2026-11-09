# MySQL / MariaDB connection troubleshooting: a runnable lab + EN/TR checklists

**Connection refused, error 2002, or Access denied (1045)? Choose the next check from the actual failure.**

This kit includes isolated MySQL and MariaDB experiments, recorded results, and browser checklists for Windows PowerShell and Linux/macOS. No database credentials or private hostname are needed to use the checklists.

**[Use the English interactive guide](https://cyber-tool.org/en/port/3306?utm_source=github&utm_medium=referral&utm_campaign=mysql_connection_lab#connection-guide)** · **[Türkçe interaktif rehber](https://cyber-tool.org/tr/port/3306?utm_source=github&utm_medium=referral&utm_campaign=mysql_connection_lab#connection-guide)**

## What the experiment actually showed

Tested on **9 November 2026**, with **MySQL 8.4.13** and **MariaDB 11.4.13**, each in its own disposable Linux Docker container with `--network none` and **no published host ports**.

| Controlled change | MySQL client | MariaDB client | Next check |
| --- | --- | --- | --- |
| TCP to 127.0.0.1:3307, no listener | 2003 / HY000 | 2002 / HY000 | Listener, destination, configured port |
| TCP to 127.0.0.1:3306, deliberately wrong password | 1045 / 28000 | 1045 / 28000 | Authentication after reaching the server |
| Unix socket path deliberately absent | 2002 / HY000 | 2002 / HY000 | Socket path and transport |
| Same TCP server, correct temporary password | SELECT 1 → 1; exit 0 | SELECT 1 → 1; exit 0 | Successful control for each engine |

**The same refused connection produced different error numbers.** MariaDB used 2002 for both refused TCP and a missing socket; MySQL used 2003 for refused TCP and 2002 for the missing socket. Identify the client, transport and full error before choosing a fix. Outside this controlled lab, 1045 does not by itself prove a wrong password; user/host matching and authentication configuration also matter.

These are eight verified synthetic outcomes, not customer incidents. Native Windows clients, separate application-container networking and TLS failure modes were not tested by this lab.

## Run it yourself

Requires Python 3 and an existing Docker installation. Download the repository files or the [bilingual kit](https://cyber-tool.org/downloads/cybertool-mysql-kit.zip), then run either engine:

```sh
docker pull mysql:8.4
python3 mysql_connection_lab.py --engine mysql

docker pull mariadb:11.4
python3 mysql_connection_lab.py --engine mariadb
```

Each invocation creates one temporary container, runs four checks, verifies their outcomes, and removes the container and temporary database. The limits are 1 CPU and 1 GB of memory for MySQL or 512 MB for MariaDB. Random credentials are not printed or saved to disk; they exist in temporary process/container environments. Image downloads need internet; the running lab has no external network. No existing database or container is modified.

`mysql-server-lab-results.json` and `lab-results.json` record the respective client versions, image digests, error codes, successful controls and cleanup. Image tags can move. To reproduce a recorded image, pull its digest and tag it locally as the corresponding `mysql:8.4` or `mariadb:11.4` before running the script.

## Use the checklist without Docker

Download the files together and open `demo-en.html` or `demo-tr.html`. The HTML runs no commands, makes no database connections and sends no analytics. External guide/reference links need internet.

1. Choose the full error: refused, timeout, authentication, socket, or DNS.
2. Choose where the failing application runs and which client it uses.
3. Generate the checks, copy/download the text, or share a case-only link.
4. Run appropriate checks in your own authorized application environment.

Chrome verification used a local HTTP preview. Direct `file://` opening was not independently verified in the available browser environment. Clipboard permissions vary; generated text stays visible for manual copying.

## A common Docker trap

For separate application and database containers, `127.0.0.1` in the application points to the application container. On a shared Compose network, use the database service name and **container** port, for example `db:3306`. A host mapping of `3307:3306` does not change that to `db:3307`.

Our lab deliberately runs the client **inside the database container**, where loopback is correct. A successful lab or external port check does not prove your application's network path works.

## Türkçe

Bu paket, aynı bağlantı reddinin MySQL 8.4.13 istemcisinde 2003, MariaDB 11.4.13 istemcisinde 2002 verdiğini gösterir. Motor başına dört kontrol geçti. `mysql-server-lab-results.json` ve `lab-results.json` gerçek deney sonuçlarını, `mysql_connection_lab.py` tekrarlama betiğini içerir. Windows örnek vakaları ise açıkça varsayımsal olarak etiketlenmiştir.

Docker olmadan `demo-tr.html` üzerinden hata ve ortam seçip kontrol listenizi oluşturabilirsiniz. Sunucu, kullanıcı veya parola girilmez. [Güncel Türkçe rehberde](https://cyber-tool.org/tr/port/3306?utm_source=github&utm_medium=referral&utm_campaign=mysql_connection_lab#mysql-connection-lab) sonuçların yorumunu ve konteynerlerde localhost/port ayrımını okuyun.

## Sources and scope

- [MySQL connection troubleshooting](https://dev.mysql.com/doc/refman/8.4/en/can-not-connect-to-server.html)
- [MySQL Access denied](https://dev.mysql.com/doc/refman/8.4/en/error-access-denied.html)
- [Docker Compose networking](https://docs.docker.com/compose/how-tos/networking/)
- [MariaDB official image environment variables](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/mariadb-server-docker-official-image-environment-variables)

Maintained for **cyber-tool.org**. This repository links to our own site; it is not an independent recommendation. Content and code were prepared with AI assistance, checked against the linked documentation, and tested as described above. The web-guide links use a fixed campaign label to distinguish referrals; the offline demo itself sends no analytics. No root-cause guarantee or customer repair is claimed.
