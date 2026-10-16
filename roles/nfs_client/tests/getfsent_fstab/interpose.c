/* DYLD_INSERT_LIBRARIES interposer: redirects fopen("/etc/fstab", ...) to
 * the scratch file named by FSTAB_REDIRECT_TARGET, so prog.c's getfsent(3)
 * reads a disposable file instead of the real /etc/fstab. getfsent's own
 * libc implementation opens the path with fopen(); it never touches
 * /etc/fstab for any other path, so no other interposition is needed. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const char *redirect_path(const char *path) {
  const char *target = getenv("FSTAB_REDIRECT_TARGET");
  const char *src = getenv("FSTAB_REDIRECT_SRC");
  if (!target || !src) return path;
  if (strcmp(path, src) == 0) return target;
  return path;
}

FILE *my_fopen(const char *path, const char *mode) {
  return fopen(redirect_path(path), mode);
}

typedef struct interpose_s {
  void *new_func;
  void *orig_func;
} interpose_t;

__attribute__((used)) static const interpose_t interposers[]
    __attribute__((section("__DATA,__interpose"))) = {
        {(void *)my_fopen, (void *)fopen},
};
