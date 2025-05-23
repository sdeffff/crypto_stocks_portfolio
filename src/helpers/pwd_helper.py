import bcrypt


async def hashPwd(plainPwd: str):
    bytePwd = plainPwd.encode('utf-8')
    saltRounds = bcrypt.gensalt()

    return bcrypt.hashpw(bytePwd, saltRounds)


async def comparePwds(plainPwd: str, hashedPwd: str):
    plainPwdBytes = plainPwd.encode('utf-8')
    hashedPwdBytes = hashedPwd.encode('utf-8')

    return bcrypt.checkpw(plainPwdBytes, hashedPwdBytes)
