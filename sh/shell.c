
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include "retargetserial.h"

#ifdef TDE_SUPPORT
#include "sys.h"
#include "shell.h"

#define LOG_MSG	SH_Printf
#define SH_MAX_CMD_LEN (64)

#ifndef UNIT_TST_SUPPORT
#define CMD_SET_MAX_NUM 1
#else
#define CMD_SET_MAX_NUM 2
#endif

typedef struct __sh_module__
{
	char *pCmdBuf;
	uint8_t uCurId;
	uint8_t uCmdReady;
	SH_IDLE_FUNC pIdleFunc;
	PSH_CMD_SET pCmdSetTable[CMD_SET_MAX_NUM];
} SH_MODULE, *PSH_MODULE;

static SH_MODULE theM;

static int32_t SH_CmdProc(PSH_CMD_SET pCmdSet, char *pCmd, uint8_t uLen);
static void SH_Check( void );
static void SH_Idle( void );

int32_t SH_Init(void)
{
	int32_t i;
	theM.pCmdBuf = malloc(SH_MAX_CMD_LEN);

	if(NULL == theM.pCmdBuf)
		return -1;	
	memset(theM.pCmdBuf, 0 ,SH_MAX_CMD_LEN);
	theM.uCurId = 0;
	theM.uCmdReady = 0;
	theM.pIdleFunc = NULL;
	for(i = 0; i < CMD_SET_MAX_NUM; i++ )
		theM.pCmdSetTable[i] = NULL;

	return 0;
}

int32_t SH_RegCmds(PSH_CMD_SET pCmdTable)
{
	int32_t i;
	for(i = 0; i < CMD_SET_MAX_NUM; i++ )
	{
		if( NULL ==  theM.pCmdSetTable[i])
		{
			theM.pCmdSetTable[i] = pCmdTable;
			return 0;
		}
	}
	return -1;
}

void SH_RegIdleFunc(SH_IDLE_FUNC pFunc)
{
	theM.pIdleFunc = pFunc;
}

void SH_Deinit(void)
{

	if(NULL != theM.pCmdBuf)
		free(theM.pCmdBuf);
	return;
}

int32_t SH_Cmd( void )
{
	int32_t i;
	int32_t nRet = 0;
	SH_Check( );
	if(theM.uCmdReady)
	{
		for(i = 0; i < CMD_SET_MAX_NUM; i++ )
		{
			nRet = SH_CmdProc(theM.pCmdSetTable[i], theM.pCmdBuf, theM.uCurId);
			if(0 == nRet)
				break;
		}
		if(0 > nRet)
			LOG_MSG("The cmd %s isn't supported.\r\n",theM.pCmdBuf );
		theM.uCmdReady = 0;
		theM.uCurId = 0;
	}
	SH_Idle();
	return 0;
}

int32_t SH_Get3ByteParams(void *pArg, uint8_t *uP0, uint8_t *uP1, uint8_t *uP2)
{
	char *pA = pArg;
	char *p;
	p = SH_GetArg(&pA);
	if(NULL == p )
	{
		return -1;
	}
	*uP0 = (uint8_t)atoi(p);

	p = SH_GetArg(&pA);
	if(NULL == p )
	{
		return -2;
	}
	*uP1 = atoi(p);

	p = SH_GetArg(&pA);
	if(NULL == p )
	{
		return -3;
	}
	*uP2 = atoi(p);
	return 0;
}



char *SH_GetArg( char **pArg)
{
	char *p = *pArg;
	char *pF = NULL;
	if(NULL == p)
		return NULL;
	while (' ' == *p )
	{
		p++;
		if('\0' == *p)
			return pF;
	}

	pF = p;
	while(' ' != *p)
    {
		p++;
		if('\0' == *p)
		{
			*pArg = NULL;
			return pF;
		}
	}
	*p = '\0';
	p++;
	*pArg = p;
	return pF;
}

int32_t SH_GetWord(void *pArg,uint32_t *uVal)
{
	char *pA = pArg;
	*uVal = atoi(pA);
	return 0;
}


static void SH_Check( void )
{
	int c;
	while(1)
	{
		c = RETARGET_ReadChar( );
		if(-1 == c)
			return;
		LOG_MSG("%c",(char)c);
		if( 0x0D == c)
		{
			theM.pCmdBuf[theM.uCurId] = '\0';
			theM.uCmdReady = 1;
		}
		else
		{
			if((theM.uCurId < (SH_MAX_CMD_LEN -1))&& (0x0A != c))
				theM.pCmdBuf[theM.uCurId++] = (char)c;
		}
	}
		
}


static int32_t SH_ParseCmd(char *pSrc, char *pCmdLine, char **pArg)
{
	uint8_t i = 0;
	*pArg = NULL;
	for(i = 0; i < strlen(pSrc); i++)
	{
		if(pSrc[i]!= pCmdLine[i])
			return -1;
	}
	if(' ' != pCmdLine[i]&& '\0'!= pCmdLine[i] )
		return -2;
	if('\0' != pCmdLine[i])
		*pArg = &pCmdLine [i + 1];
	return 0;
}

static int32_t SH_CmdProc(PSH_CMD_SET pCmdSet, char *pCmdLine, uint8_t uLen)
{
	int32_t i;
	char *pCmdArg = NULL;
	if(NULL == pCmdLine )
		return -1;
	if(NULL == pCmdSet)
		return 0;

	for(i = 0; ; i++)
	{
		if(NULL == pCmdSet[i].pCmd)
			break;
		if( 0 == SH_ParseCmd(pCmdSet[i].pCmd, pCmdLine, &pCmdArg))
		{
			if(NULL != pCmdSet[i].pFunc)
			{
				pCmdSet[i].pFunc(pCmdArg);
				return 0;
			}
		}
	}
	if( 0 == uLen)
		return 0;
	return -2; 
}

/**
 * @brief shell idle loop
 * 
 */
static void SH_Idle( void )
{
	if(NULL != theM.pIdleFunc)
		theM.pIdleFunc();
}


