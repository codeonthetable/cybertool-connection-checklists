# MySQL / MariaDB connection troubleshooting: a runnable lab + EN/TR checklists

**Connection refused, error 2002, or Access denied (1045)? Choose the next check from the actual failure.**

This kit includes an isolated MariaDB experiment, recorded results, and browser checklists for Windows PowerShell and Linux/macOS. No database credentials or private hostname are needed to use the checklists.

**[Use the English interactive guide](https://cyber-tool.org/en/port/3306?utm_source=github&utm_medium=referral&utm_campaign=mysql_connection_lab#connection-guide)** · **[Türkçe interaktif rehber](https://cyber-tool.org/tr/port/3306?utm_source=github&utm_medium=referral&utm_campaign=mysql_connection_lab#connection-guide)**

## What the experiment actually showed

Tested on **4 November 2026**, with **MariaDB 11.4.13**, inside a disposable Linux Docker container with `--network none` and **no published host ports**:

| Controlled change | Observed result | What to investigate |
| --- | --- | --- |
| TCP to 127.0.0.1:3307, no listener | 2002 / HY000 | Listener, destination, configured port |
| TCP to 127.0.0.1:3306, deliberately wrong password | 1045 / 28000 | Authentication after reaching the server |
| Unix socket path deliberately absent | 2002 / HY000 | Socket path and transport |
| Same TCP server, correct temporary password | `SELECT 1` returned `1`, exit 0 | Successful control for this lab |

**2002 is not enough to identify the broken layer.** This MariaDB client used it for both refused TCP and a missing Unix socket. MySQL documentation also describes 2003/10061 for connection refusal. Read the complete error and transport, not only the number. Outside this controlled lab, 1045 does not by itself prove a wrong password; user/host matching and authentication configuration also matter.

These are reproducible synthetic tests, not customer incidents. MySQL server and native Windows-client execution are not covered by this lab.

## Run it yourself

Requires Python 3 and an existing Docker installation. Download the repository files or the [bilingual kit](https://cyber-tool.org/downloads/cybertool-mysql-kit.zip), then run:

```sh
docker pull mariadb:11.4
python3 mysql_connection_lab.py
```

The script creates one temporary container, limits it to 512 MB / 1 CPU, runs four checks, verifies their outcomes, and removes the container and temporary database. It generates an ephemeral password without printing it. Docker requires enough memory for the database. The initial image download needs internet; the running lab has no external network. No existing database or container is modified.

`lab-results.json` records the client version, actual image digest, expected error codes, successful control and cleanup. The `11.4` image tag can move. To reproduce the recorded image, first pull its digest from that file and tag it locally as `mariadb:11.4`, then run the script.

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

Bu paket, bağlantı reddi / 2002 / 1045 ayrımını dört kontrollü MariaDB deneyiyle gösterir. `lab-results.json` gerçek deney sonuçlarını, `mysql_connection_lab.py` tekrarlama betiğini içerir. Windows örnek vakaları ise açıkça varsayımsal olarak etiketlenmiştir.

Docker olmadan `demo-tr.html` üzerinden hata ve ortam seçip kontrol listenizi oluşturabilirsiniz. Sunucu, kullanıcı veya parola girilmez. [Güncel Türkçe rehberde](https://cyber-tool.org/tr/port/3306?utm_source=github&utm_medium=referral&utm_campaign=mysql_connection_lab#mysql-connection-lab) sonuçların yorumunu ve konteynerlerde localhost/port ayrımını okuyun.

## Sources and scope

- [MySQL connection troubleshooting](https://dev.mysql.com/doc/refman/8.4/en/can-not-connect-to-server.html)
- [MySQL Access denied](https://dev.mysql.com/doc/refman/8.4/en/error-access-denied.html)
- [Docker Compose networking](https://docs.docker.com/compose/how-tos/networking/)
- [MariaDB official image environment variables](https://mariadb.com/docs/server/server-management/automated-mariadb-deployment-and-administration/docker-and-mariadb/mariadb-server-docker-official-image-environment-variables)

Maintained for **cyber-tool.org**. This repository links to our own site; it is not an independent recommendation. Content and code were prepared with AI assistance, checked against the linked documentation, and tested as described above. The web-guide links use a fixed campaign label to distinguish referrals; the offline demo itself sends no analytics. No root-cause guarantee or customer repair is claimed.
