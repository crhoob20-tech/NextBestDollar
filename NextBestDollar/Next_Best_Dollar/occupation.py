SECTORS=['Not specified','Private employer','Education / nonprofit','Federal government','State / local government','Self-employed / business owner','Not currently working']
PROMPTS={
 'Education / nonprofit':'Ask your employer whether you have a pension, 403(b), or 457(b). The plan depends on the employer, not just your job title.',
 'Federal government':'Check whether you have a Thrift Savings Plan (TSP) and a pension benefit.',
 'State / local government':'Check for a pension and a 457(b) or other employer-sponsored savings plan.',
 'Self-employed / business owner':'Business owners may establish a solo 401(k), SEP IRA or SIMPLE IRA, depending on business and employee circumstances. Confirm which you actually have.',
 'Private employer':'Check whether your employer offers a 401(k), pension, SIMPLE IRA or another retirement plan.',
}
def prompt(sector):return PROMPTS.get(sector,'You can add an existing retirement account even if you are not currently working.')
