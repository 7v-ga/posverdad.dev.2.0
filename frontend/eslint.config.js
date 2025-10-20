import next from 'eslint-config-next'
import prettier from 'eslint-config-prettier'


export default [
...next,
prettier,
{
rules: {
'@next/next/no-html-link-for-pages': 'off',
'react/react-in-jsx-scope': 'off'
}
}
]