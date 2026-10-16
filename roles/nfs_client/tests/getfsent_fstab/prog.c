/* Minimal driver over the real macOS getfsent(3)/setfsent(3): prints one
 * "ENTRY ..." line per fstab row the stock parser accepts, then a COUNT
 * line. Run with the fstab_interpose.c dylib loaded (DYLD_INSERT_LIBRARIES)
 * so fopen("/etc/fstab", ...) is redirected to a scratch file instead of
 * reading the real one. */
#include <fstab.h>
#include <stdio.h>

int main(void) {
  if (!setfsent()) {
    fprintf(stderr, "ERROR setfsent failed\n");
    return 1;
  }
  struct fstab *fs;
  int n = 0;
  while ((fs = getfsent())) {
    printf("ENTRY spec=[%s] file=[%s] type=[%s] opts=[%s] freq=%d passno=%d\n",
           fs->fs_spec, fs->fs_file, fs->fs_type, fs->fs_mntops, fs->fs_freq,
           fs->fs_passno);
    n++;
  }
  endfsent();
  printf("COUNT=%d\n", n);
  return 0;
}
