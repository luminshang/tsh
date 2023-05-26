/*****************************************************************************
 Copyright (c) 2022 Movano Inc. 
 Module/File Name:
	tdecmd.h
 Abstract:
	TDE command header file.
******************************************************************************/

#ifndef __TDE_CMD_H__
#define __TDE_CMD_H__
#include <stdint.h> 

#ifdef TDE_SUPPORT

/**
 * @brief TDE init
 * 
 * @return int32_t 0:success others: fail
*/
int32_t TDEC_Init(void);

/**
 * @brief TDE event process
 * 
 * @param uExtEvt event value
* @return int32_t 0:success others: fail
 */
int32_t TDEC_OnEvt(uint32_t uExtEvt);
#endif //TDE_SUPPORT

#endif //__TDE_CMD_H__
