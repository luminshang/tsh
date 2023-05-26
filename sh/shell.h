
#ifndef __SH_H__
#define __SH_H__
#include <stdint.h>
#include <stdio.h>

typedef int32_t (*SH_CMD_FUNC)(void *pArg);
typedef void (*SH_IDLE_FUNC)(void);

typedef struct __sh_cmd_set__
{
	char *pCmd;
	SH_CMD_FUNC pFunc;
	char *pHelp;
} SH_CMD_SET, *PSH_CMD_SET;

#define SH_Printf printf

int32_t SH_Init(void);


void SH_Deinit(void);


int32_t SH_Cmd( void );


int32_t SH_RegCmds(PSH_CMD_SET pCmdTable);


void SH_RegIdleFunc(SH_IDLE_FUNC pFunc);

int32_t SH_Get3ByteParams(void *pArg, uint8_t *uP0, uint8_t *uP1, uint8_t *uP2);
char *SH_GetArg( char **pArg);
int32_t SH_GetWord(void *pArg,uint32_t *uVal);

//void SH_Printf(char *pTxt, ...);


#endif //__SH_H__
