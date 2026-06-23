# Nautobot Dev Tips

## JobResult Files and FileProxy API

Nautobot Jobs can publish downloadable files with `self.create_file()`. The
generated files may be visible from the JobResult UI even when the JobResult API
response does not embed any file list.

Observed with Nautobot API version 3.1:

- `GET /api/extras/job-results/<uuid>/` returns JobResult status and metadata,
  but not the generated file proxies.
- GUI downloads may add a random suffix to the saved filename, for example
  `dnsmasq-records_FuWxFgS.conf`, even if the Job called
  `self.create_file("dnsmasq-records.conf", ...)`.
- Filtering `/api/extras/file-proxies/` with guessed parameters such as
  `job_result=<uuid>` or `name=<filename>` can return `400 Bad Request` if the
  filter names do not match the Nautobot version's actual API filter set.

For automation, avoid relying on undocumented FileProxy filters. Prefer one of
these approaches:

1. Use FileProxy API filters only after confirming the exact filter names in the
   target Nautobot version.
2. Otherwise, fetch `/api/extras/file-proxies/` and select the matching object
   client-side by checking for the JobResult UUID and the expected filename
   pattern in the returned JSON.

For the nintent dnsmasq export, the Job writes `dnsmasq-records.conf`, but the
client-side match should also accept Nautobot's suffixed download name pattern:

```text
dnsmasq-records(_[A-Za-z0-9]+)?\.conf
```

If a Job succeeds and the file is downloadable from the GUI, but Ansible fails
with `HTTP status=400` while looking up `/api/extras/file-proxies/`, suspect an
invalid FileProxy query parameter before suspecting the Job or file generation
logic.
