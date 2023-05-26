#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "sys.h"


#define LOG_MSG SH_Printf

static int32_t GetVer (void *pArg);

const static SH_CMD_SET theCmdTable[] =
{
	{"get_ver", GetVer, ""},

	{NULL,NULL, ""}
};

int32_t TDEC_Init(void)
{
	SH_RegCmds((PSH_CMD_SET)theCmdTable);
	return 0;
}

int32_t TDEC_OnEvt(uint32_t uExtEvt)
{
	TOB_OnEvt(uExtEvt);
	return 0;
}

static int32_t GetVer (void *pArg)
{
	char *pVer = NULL;
	pVer = SVC_GetFWVer();
	if(NULL == pVer)
	{
		LOG_MSG("FWVER: FAILED. Can not read the firmware version.\r\n");
		return -1;
	}
	LOG_MSG("FWVER: PASSED. Firmware version: %s\r\n", pVer);
	return 0;
}


